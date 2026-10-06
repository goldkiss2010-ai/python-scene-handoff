from pathlib import Path

from python_scene_handoff.pixel_plane import (
    PixelPlaneSpec,
    build_pixel_plane_package,
    write_cfa_svg,
    write_hot_pixel_svg,
)


def test_default_spec_is_four_megapixels() -> None:
    spec = PixelPlaneSpec()
    assert spec.width == 2000
    assert spec.height == 2000
    assert spec.pixel_count == 4_000_000
    assert (spec.hot_x, spec.hot_y) == (1000, 1000)
    assert spec.hot_cfa_channel == "R"


def test_svg_keeps_exact_sensor_coordinates(tmp_path: Path) -> None:
    spec = PixelPlaneSpec(width=8, height=6, hot_x=3, hot_y=4, cfa_pattern="RGGB")

    cfa = write_cfa_svg(spec, tmp_path / "cfa.svg")
    hot = write_hot_pixel_svg(spec, tmp_path / "hot.svg", color="#FF0000")

    cfa_text = cfa.read_text(encoding="utf-8")
    hot_text = hot.read_text(encoding="utf-8")

    assert 'viewBox="0 0 8 6"' in cfa_text
    assert 'pattern id="cfa" width="2" height="2"' in cfa_text
    assert 'x="3" y="4" width="1" height="1"' in hot_text
    assert 'fill="#FF0000"' in hot_text


def test_package_emits_separate_background_and_hot_pixel(tmp_path: Path) -> None:
    package = build_pixel_plane_package(
        tmp_path,
        spec=PixelPlaneSpec(width=20, height=10, hot_x=7, hot_y=2),
        birth_time=2.0,
    )

    assert package.cfa_svg is not None
    assert package.cfa_svg.exists()
    assert package.hot_pixel_svg.exists()
    assert package.ae_jsx.exists()
    assert package.manifest.exists()

    jsx = package.ae_jsx.read_text(encoding="utf-8")
    assert 'bgLayer.name = "CFA_BACKGROUND"' in jsx
    assert 'hotLayer.name = "HOT_PIXEL"' in jsx
    assert 'fx.name = "Hot Pixel On"' in jsx
    assert "checkbox.setValueAtTime(2, 1);" in jsx
