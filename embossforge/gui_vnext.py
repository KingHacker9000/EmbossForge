from __future__ import annotations

from dataclasses import replace
import sys
from pathlib import Path

from . import gui as legacy
from .relief import ArtworkMode, SourceInterpretation
from .shaded_reference import looks_continuously_shaded


QtCore = legacy.QtCore
QtGui = legacy.QtGui
QtWidgets = legacy.QtWidgets


class MainWindow(legacy.MainWindow):
    """Production desktop window with the completed vNext relief workflow."""

    def __init__(self):
        self._pending_shaded_request = None
        self._preview_only = False
        self._generation_elapsed_s = 0
        self._generation_timer = None
        super().__init__()
        self._generation_timer = QtCore.QTimer(self)
        self._generation_timer.setInterval(1000)
        self._generation_timer.timeout.connect(self._tick_generation_status)

    def _style_changed(self) -> None:
        self._pending_shaded_request = None
        super()._style_changed()

    def _source_changed(self) -> None:
        if self.emboss_style.currentData() != ArtworkMode.RELIEF.value:
            return
        shaded = self.source_interpretation.currentData() == SourceInterpretation.SHADED_REFERENCE.value
        if shaded:
            self.source_help.setText(
                "EmbossForge will remove broad lighting, isolate the motif, and synthesize an inspectable printer-aware relief map. "
                "It does not claim to reconstruct true 3D depth. You will preview the derived map before STL rendering."
            )
            self.source_help.setProperty("state", "warning")
        else:
            self.source_help.setText(
                "True height map: grayscale was authored as geometry. White is zero relief and darker tones are higher by default."
            )
            self.source_help.setProperty("state", "normal")
        self._refresh_style(self.source_help)
        self._pending_shaded_request = None
        self._update_generate_enabled()

    def _set_artwork(self, filename: str) -> None:
        self._pending_shaded_request = None
        super()._set_artwork(filename)
        path = Path(filename)
        if self.artwork_path is not None and looks_continuously_shaded(path):
            self.message.setText(
                "Artwork loaded. This raster contains substantial continuous shading; if it is a render/AI medallion, choose Variable depth → 3D-looking / shaded reference."
            )
            self.message.setProperty("state", "ready")
            self._refresh_style(self.message)

    def _update_generate_enabled(self) -> None:
        enabled = self.artwork_path is not None and self.worker is None
        self.generate_button.setEnabled(enabled)

    def _generate(self) -> None:
        if self.artwork_path is None:
            return
        request = self._request()
        shaded = (
            request.artwork_mode == ArtworkMode.RELIEF
            and request.source_interpretation == SourceInterpretation.SHADED_REFERENCE
        )
        if not shaded:
            self._pending_shaded_request = None
            self._start_generation(request, preview_only=False)
            return

        full_request = replace(request, render_stl=True)
        if self._pending_shaded_request is not None:
            candidate = replace(
                full_request,
                allow_risky=self._pending_shaded_request.allow_risky,
            )
            if self._pending_shaded_request == candidate:
                self._pending_shaded_request = None
                self._start_generation(candidate, preview_only=False)
                return

        self._pending_shaded_request = None
        self._start_generation(replace(request, render_stl=False), preview_only=True)

    def _start_generation(self, request, preview_only: bool = False) -> None:
        self._preview_only = preview_only
        self._generation_elapsed_s = 0
        if self._generation_timer is not None:
            self._generation_timer.start()
        super()._start_generation(request)
        if preview_only:
            self.generate_button.setText("Deriving preview…")
            self.message.setText(
                "Interpreting the shaded reference into an emboss-oriented height map and validating the matched pair…"
            )
            self.message.setProperty("state", "working")
            self.validation_message.setText("Deriving shared relief geometry before STL rendering…")
            self._refresh_style(self.message)
        elif request.artwork_mode == ArtworkMode.RELIEF:
            self.generate_button.setText("Rendering die STLs…")
            self.message.setText(
                "Building the shared height field, then rendering the male and female STL. Variable-depth OpenSCAD rendering can take a little while."
            )
            self.message.setProperty("state", "working")
            self._refresh_style(self.message)

    def _tick_generation_status(self) -> None:
        if self.worker is None:
            if self._generation_timer is not None:
                self._generation_timer.stop()
            return
        self._generation_elapsed_s += 1
        if self._preview_only:
            if self._generation_elapsed_s >= 15:
                self.validation_message.setText(
                    f"Still deriving/validating the relief preview… {self._generation_elapsed_s}s elapsed."
                )
            return

        request = self._last_request
        if request is not None and request.artwork_mode == ArtworkMode.RELIEF:
            if self._generation_elapsed_s >= 90:
                self.validation_message.setText(
                    f"OpenSCAD is still rendering the relief surfaces… {self._generation_elapsed_s}s elapsed. "
                    "Each render now has a 180s safety timeout. Draft height-map quality is the fastest retry option."
                )
            elif self._generation_elapsed_s >= 20:
                self.validation_message.setText(
                    f"Rendering variable-depth geometry… {self._generation_elapsed_s}s elapsed. This is slower than simple embossing."
                )

    def _worker_finished(self) -> None:
        if self._generation_timer is not None:
            self._generation_timer.stop()
        super()._worker_finished()

    def _generated(self, result) -> None:
        if self._preview_only and result.source_interpretation == SourceInterpretation.SHADED_REFERENCE:
            self.result = result
            self._preview_only = False
            self._pending_shaded_request = replace(self._last_request, render_stl=True)
            preview = result.outputs.get("derived_relief_preview", result.normalized_artwork)
            self._render_preview(preview)
            self.preview_note.setText(
                "Showing EmbossForge's derived relief preview (white = higher in this preview). The original image was interpreted, not treated as literal depth."
            )

            caution_count = sum(
                1 for finding in result.validation.findings if finding.severity.value in {"caution", "high"}
            )
            self.validation_message.setText(
                "✓ Derived pair geometry validated"
                + (f" · {caution_count} paper/quality caution(s)" if caution_count else "")
            )
            self.validation_message.setProperty("state", "warning" if caution_count else "success")
            self._refresh_style(self.validation_message)

            self.message.setText(
                "Derived relief preview ready. Review it above, then click Accept preview & generate STLs. "
                "Changing any settings will automatically regenerate the preview first."
            )
            self.message.setProperty("state", "ready")
            self._refresh_style(self.message)
            self.generate_button.setText("Accept preview & generate STLs")
            self.open_folder_button.hide()
            return

        self._preview_only = False
        self._pending_shaded_request = None
        super()._generated(result)
        if result.source_interpretation == SourceInterpretation.SHADED_REFERENCE:
            self.preview_note.setText(
                "Derived shaded-reference relief accepted. The saved manifest records the interpretation method and all intermediate maps."
            )

    def _failed(self, message: str) -> None:
        was_preview = self._preview_only
        self._preview_only = False

        if was_preview and "high experimental paper-risk" in message and self._last_request is not None:
            self.message.setText(
                "The derived geometry can mate, but EmbossForge found a high experimental paper-damage risk."
            )
            self.message.setProperty("state", "warning")
            self._refresh_style(self.message)

            box = QtWidgets.QMessageBox(self)
            box.setWindowTitle("High paper-risk warning")
            box.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            box.setText("This interpreted relief may be harsh on the selected paper.")
            box.setInformativeText(
                message
                + "\n\nGenerate anyway accepts only the paper-risk heuristic. Die-to-die interference and invalid geometry remain non-overrideable."
            )
            box.addButton("Go back and adjust", QtWidgets.QMessageBox.ButtonRole.RejectRole)
            generate_anyway = box.addButton("Generate preview anyway", QtWidgets.QMessageBox.ButtonRole.AcceptRole)
            box.exec()
            if box.clickedButton() is generate_anyway:
                self._start_generation(
                    replace(self._last_request, allow_risky=True, render_stl=False),
                    preview_only=True,
                )
            else:
                self._pending_shaded_request = None
                self._update_generate_enabled()
            return

        if "high experimental paper-risk" not in message:
            self._pending_shaded_request = None
        super()._failed(message)


def main() -> int:
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    app.setApplicationName("EmbossForge")
    app.setOrganizationName("EmbossForge")
    app.setFont(QtGui.QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
