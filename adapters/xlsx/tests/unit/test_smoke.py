from bims.prism.adapters.xlsx import build_report


def test_skeleton_build(tmp_path):
    data = build_report(None)  # dummy arg

    outfile = tmp_path / "skeleton.xlsx"
    outfile.write_bytes(data)

    assert data[:2] == b"PK"      # XLSX = ZIP archive
    assert len(data) > 200        # не пустой
