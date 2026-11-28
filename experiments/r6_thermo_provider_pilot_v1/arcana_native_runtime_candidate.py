#!/usr/bin/env python3
"""Private native deployment of the exact historical ELF code and dependencies.
No source compilation, package install, SIMD enablement or physical admission.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import re
import shutil
import struct
import subprocess


def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def in_root(root,reference):
    todo=list(PurePosixPath('/'+reference.lstrip('/')).parts)[1:];current=root;links=0
    while todo:
        part=todo.pop(0)
        if part=='.':continue
        if part=='..':current=current.parent;continue
        candidate=current/part
        if candidate.is_symlink():
            links+=1
            if links>40:raise ValueError('SYMLINK_LOOP')
            dest=os.readlink(candidate)
            if dest.startswith('/'):current=root
            todo=[v for v in PurePosixPath(dest).parts if v!='/']+todo
        else:current=candidate
        if not current.is_relative_to(root):raise ValueError('ROOT_ESCAPE')
    return current


def text_sha(p):
    out=subprocess.check_output(['readelf','-SW',str(p)],text=True)
    m=re.search(r'\[\s*\d+\]\s+\.text\s+PROGBITS\s+[a-f0-9]+\s+([a-f0-9]+)\s+([a-f0-9]+)',out)
    if not m:raise ValueError('ELF_TEXT_SECTION')
    with p.open('rb') as f:f.seek(int(m[1],16));return hashlib.sha256(f.read(int(m[2],16))).hexdigest()


def inherit_search_path(p):
    # DT_RPATH=15 and DT_RUNPATH=29 from the installed ELF ABI header.
    header=Path('/usr/include/elf.h').read_text()
    for name,val in (('DT_RPATH',15),('DT_RUNPATH',29)):
        if not re.search(r'^#define\s+'+name+r'\s+'+str(val)+r'\b',header,re.M):raise ValueError('ELF_ABI')
    with p.open('r+b') as f:
        h=f.read(64)
        if h[:6]!=b'\x7fELF\x02\x01' or struct.unpack_from('<H',h,18)[0]!=62:raise ValueError('ELF_NOT_X86_64_LE')
        phoff=struct.unpack_from('<Q',h,32)[0];size,n=struct.unpack_from('<HH',h,54);changed=0
        for j in range(n):
            f.seek(phoff+j*size);ph=f.read(size)
            if struct.unpack_from('<I',ph,0)[0]!=2:continue
            offset=struct.unpack_from('<Q',ph,8)[0];length=struct.unpack_from('<Q',ph,32)[0]
            for k in range(0,length,16):
                f.seek(offset+k);tag=struct.unpack('<q',f.read(8))[0]
                if tag==29:f.seek(offset+k);f.write(struct.pack('<q',15));changed+=1
        if changed!=1:raise ValueError('EXPECTED_ONE_RUNPATH')


def prepare(base,out):
    state=base/'ARCANA_ASPECT_TOOLS/udocker-state'
    root=(state/'containers/arcana-aspect-v310/ROOT').resolve()
    if out.exists() or out.is_relative_to(base/'ARCANA_ASPECT_TOOLS'):raise ValueError('PRIVATE_OUTPUT')
    out.mkdir();(out/'lib').mkdir();(out/'bin').mkdir();(out/'share').symlink_to(root/'usr/share')
    links={}
    for directory in ('usr/lib/x86_64-linux-gnu','usr/lib/x86_64-linux-gnu/openmpi/lib','usr/lib','home/dealii/aspect/lib'):
        p=root/directory
        if not p.is_dir():continue
        for item in sorted(p.glob('*.so*')):
            target=in_root(root,str(item.relative_to(root)))
            if target.is_file() and item.name not in links:
                (out/'lib'/item.name).symlink_to(target);links[item.name]=str(target)
    patch=state/'bin/patchelf-x86_64';loader=root/'usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2'
    identities={}
    names=['aspect-release','orterun','orted','ompi_info','bash','taskset','grep','cut']
    for name in names:
        source=root/('home/dealii/aspect/bin/aspect-release' if name=='aspect-release' else 'usr/bin/'+name)
        source=in_root(root,str(source.relative_to(root)));dest=out/'bin'/name
        shutil.copyfile(source,dest);dest.chmod(0o755)
        subprocess.run([str(patch),'--set-interpreter',str(loader),'--set-rpath',str(out/'lib'),str(dest)],check=True,capture_output=True)
        inherit_search_path(dest)
        original_text=text_sha(source)
        if text_sha(dest)!=original_text:raise RuntimeError('APPLICATION_TEXT_CHANGED')
        identities[name]={'source':str(source),'source_sha256':sha(source),'private_sha256':sha(dest),'text_sha256':original_text,'text_exact':True}
    result={'scope':'NATIVE_RELOCATION_CANDIDATE_ONLY','application_rebuild':False,'SIMD_enabled':False,
        'changes':'private ELF interpreter/search paths only; exact historical dependencies via private symlink farm',
        'binary_identity':identities,'dependency_links':links,'loader_sha256':sha(loader),'patch_tool_sha256':sha(patch)}
    with (out/'IDENTITY.json').open('x') as f:json.dump(result,f,indent=2,sort_keys=True)
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();print(json.dumps(prepare(a.base.resolve(),a.output.resolve()),indent=2))
if __name__=='__main__':main()
