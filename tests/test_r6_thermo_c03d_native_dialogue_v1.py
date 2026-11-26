import json
import sys
import pytest
from experiments.r6_thermo_provider_pilot_v1 import c03d_native_dialogue as d

W966=(b"**warning ver966** EoS code 1 for O2 in data file hp02ver.dat requires\n"
      b"volumetric data. The code will automatically be set to 0, a G(Pr,T) EoS\n")
W968=(b"**warning ver968** O2 is a name reserved for fluid species but the EoS flag\n"
      b"for O2 in hp02ver.dat is a G(Pr,T) EoS appropriate only for calculations as a\n"
      b"function of the activity or fugacity of O2.\n")


def test_two_specific_warnings_do_not_consume_bulk_or_pt():
    state=d.Dialogue()
    raw=d.PROJECT
    assert state.next_response(raw)==b"c03d\n"
    raw+=W966+d.WARNING
    assert state.next_response(raw)==b"y\n"
    raw+=W968+d.WARNING
    assert state.next_response(raw)==b"y\n"
    raw+=d.BULK
    assert state.next_response(raw)==b"n\n"
    raw+=d.PT
    assert state.next_response(raw)==b"0 0\n"
    assert state.next_response(raw) is None
    assert state.acknowledged==["966","968"]


def test_unknown_warning_is_not_accepted():
    state=d.Dialogue()
    assert state.next_response(d.PROJECT)==b"c03d\n"
    with pytest.raises(ValueError,match="UNAPPROVED_INTERACTIVE_WARNING"):
        state.next_response(d.PROJECT+W966.replace(b"for O2",b"for H2")+d.WARNING)
    assert state.acknowledged==[]


def test_partial_prompt_and_out_of_order_pt():
    state=d.Dialogue()
    assert state.next_response(d.PROJECT[:-3]) is None
    assert state.next_response(d.PROJECT)==b"c03d\n"
    with pytest.raises(ValueError,match="UNEXPECTED_PROMPT"):
        state.next_response(d.PROJECT+d.PT)


def test_repeated_warning_rejected():
    state=d.Dialogue()
    raw=d.PROJECT
    state.next_response(raw)
    raw+=W966+d.WARNING
    state.next_response(raw)
    with pytest.raises(ValueError,match="UNAPPROVED_INTERACTIVE_WARNING"):
        state.next_response(raw+W966+d.WARNING)


def test_real_subprocess_fake_native_protocol(tmp_path):
    # Simulates the blocking provider, not its thermodynamics.
    script=tmp_path/"fake.py"
    steps=[(d.PROJECT,b"c03d"),(W966+d.WARNING,b"y"),(W968+d.WARNING,b"y"),
           (d.BULK,b"n"),(d.PT,b"0 0")]
    script.write_text("import sys\nfor prompt,expected in "+repr(steps)+":\n"
        " sys.stdout.buffer.write(prompt+b'\\n');sys.stdout.flush()\n"
        " assert sys.stdin.buffer.readline().strip()==expected\n"
        "assert not sys.stdin.buffer.read()\n")
    limits={"address_space_limit_bytes":4*1024**3,"file_size_limit_bytes":16*1024**2,"walltime_s":10}
    result=d.launch_dialogue([sys.executable,script],tmp_path,limits)
    assert result["exit_code"]==0
    assert (tmp_path/"DIALOGUE_STDIN.log").read_bytes()==b"c03d\ny\ny\nn\n0 0\n"
    z=json.loads((tmp_path/"DIALOGUE.json").read_text())
    assert z["state"]=="SENTINEL_SENT" and z["scientific_warning_acceptance"] is False


def test_unknown_warning_subprocess_is_preserved(tmp_path):
    script=tmp_path/"fake.py"
    steps=[(d.PROJECT,b"c03d"),(b"**warning ver123** unknown\n"+d.WARNING,b"y")]
    script.write_text("import sys\nfor prompt,expected in "+repr(steps)+":\n"
        " sys.stdout.buffer.write(prompt+b'\\n');sys.stdout.flush()\n"
        " assert sys.stdin.buffer.readline().strip()==expected\n")
    limits={"address_space_limit_bytes":4*1024**3,"file_size_limit_bytes":16*1024**2,"walltime_s":10}
    with pytest.raises(ValueError,match="UNAPPROVED_INTERACTIVE_WARNING"):
        d.launch_dialogue([sys.executable,script],tmp_path,limits)
    assert (tmp_path/"DIALOGUE_STDIN.log").read_bytes()==b"c03d\n"
    assert json.loads((tmp_path/"DIALOGUE.json").read_text())["error"]
