#!/usr/bin/env python3
"""Render plots only from a retained BW1_F2A_AGGREGATES.csv; never invent data."""
from __future__ import annotations
import argparse
import csv
from pathlib import Path


def load_aggregates(path: Path):
    with Path(path).open(newline="", encoding="utf-8") as stream:
        rows=list(csv.DictReader(stream))
    if not rows or not {"kind","bin_x","bin_y","count"}.issubset(rows[0]):
        raise ValueError("aggregate CSV is empty or has an invalid schema")
    known={"heatmap","heatmap_valid","matrix_log10_abs","diagonal_log10_abs","dominance_log10_ratio_quarter_decade","forcing_log10_abs"}
    if any(row["kind"] not in known for row in rows): raise ValueError("unknown aggregate data kind")
    return rows


def render(path: Path, output_dir: Path) -> list[Path]:
    import matplotlib.pyplot as plt
    import numpy as np
    rows=load_aggregates(path); output_dir=Path(output_dir); output_dir.mkdir(parents=True,exist_ok=True)
    created=[]
    heat=np.zeros((256,256),dtype=np.int64); valid=np.zeros((256,256),dtype=np.int64)
    for row in rows:
        if row["kind"]=="heatmap": heat[int(row["bin_y"])-1,int(row["bin_x"])-1]=int(row["count"])
        elif row["kind"]=="heatmap_valid": valid[int(row["bin_y"])-1,int(row["bin_x"])-1]=int(row["count"])
    density=np.divide(heat,valid,out=np.zeros((256,256),dtype=float),where=valid>0)
    fig,ax=plt.subplots(); im=ax.imshow(density,origin="lower",interpolation="nearest",aspect="auto",vmin=0,vmax=1)
    ax.set(xlabel="Mathematical column bin j",ylabel="Mathematical row bin i",title="Nonzero density of A in mathematical (i,j) bins")
    fig.colorbar(im,ax=ax,label="nonzero / valid physical coefficient slots"); p=output_dir/"matrix_sparsity_heatmap.png"; fig.savefig(p,dpi=160,bbox_inches="tight"); plt.close(fig); created.append(p)
    series=[("matrix_log10_abs","matrix_coefficient_magnitude.png","log10 |Aij|","nonzero coefficients"),
            ("diagonal_log10_abs","diagonal_distribution.png","log10 |Aii|","diagonal entries"),
            ("dominance_log10_ratio_quarter_decade","diagonal_dominance_distribution.png","ratio bin (quarter decade; 129 undefined, 130 +inf)","rows"),
            ("forcing_log10_abs","forcing_distribution.png","log10 |fi|","forcing components")]
    for kind,name,xlabel,ylabel in series:
        data=[(int(r["bin_x"]),int(r["count"])) for r in rows if r["kind"]==kind]
        fig,ax=plt.subplots(); ax.bar([x for x,_ in data],[y for _,y in data],width=.9)
        ax.set(xlabel=xlabel,ylabel=ylabel,title=kind.replace("_"," ")); p=output_dir/name; fig.savefig(p,dpi=160,bbox_inches="tight"); plt.close(fig); created.append(p)
    return created


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("aggregate_csv",type=Path); parser.add_argument("--output-dir",type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        for path in render(args.aggregate_csv,args.output_dir): print(path)
    except Exception as exc:
        parser.exit(2,f"F2A visualization failed: {exc}\n")
    return 0


if __name__=="__main__": raise SystemExit(main())
