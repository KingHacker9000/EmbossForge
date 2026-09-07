from __future__ import annotations

import sys
from pathlib import Path

from .config import PAPER_PRESETS_MM, adventurer_5m_profile
from .generator import DieGenerationRequest, generate_die


SUPPORTED_FILTER = "Design files (*.svg *.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp)"


def _qt():
    try:
        from PySide6 import QtCore, QtGui, QtSvg, QtWidgets
    except ImportError as exc:  # pragma: no cover - optional desktop dependency
        raise RuntimeError(
            "PySide6 is required for the desktop app. Install with: pip install -e \".[gui]\""
        ) from exc
    return QtCore, QtGui, QtSvg, QtWidgets


QtCore, QtGui, QtSvg, QtWidgets = _qt()


class GenerateThread(QtCore.QThread):
    completed = QtCore.Signal(object)
    failed = QtCore.Signal(str)

    def __init__(self, request: DieGenerationRequest, parent=None):
        super().__init__(parent)
        self.request = request

    def run(self) -> None:  # pragma: no cover - Qt thread wrapper
        try:
            result = generate_die(self.request)
        except Exception as exc:
            self.failed.emit(str(exc))
        else:
            self.completed.emit(result)


class ArtworkDropCard(QtWidgets.QFrame):
    fileSelected = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("dropCard")
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(150)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(7)

        self.title = QtWidgets.QLabel("Drop a design here")
        self.title.setObjectName("dropTitle")
        self.title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.subtitle = QtWidgets.QLabel("SVG, PNG or JPG  ·  click to browse")
        self.subtitle.setObjectName("muted")
        self.subtitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)
        layout.addStretch()

    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._browse()
        super().mousePressEvent(event)

    def dragEnterEvent(self, event):  # noqa: N802
        urls = event.mimeData().urls()
        if urls and _is_supported(Path(urls[0].toLocalFile())):
            event.acceptProposedAction()

    def dropEvent(self, event):  # noqa: N802
        urls = event.mimeData().urls()
        if urls:
            path = Path(urls[0].toLocalFile())
            if _is_supported(path):
                self.fileSelected.emit(str(path))
                event.acceptProposedAction()

    def _browse(self) -> None:
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Choose a design", "", SUPPORTED_FILTER)
        if filename:
            self.fileSelected.emit(filename)

    def show_file(self, path: Path) -> None:
        self.title.setText(path.name)
        self.subtitle.setText("Design loaded  ·  click to replace")


def _is_supported(path: Path) -> bool:
    return path.suffix.lower() in {".svg", ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.artwork_path: Path | None = None
        self.result = None
        self.worker: GenerateThread | None = None
        self.setWindowTitle("EmbossForge")
        self.resize(1040, 720)
        self.setMinimumSize(900, 640)
        self.setAcceptDrops(True)
        self._build_ui()
        self._apply_style()

    def _build_ui(self) -> None:
        root = QtWidgets.QWidget()
        self.setCentralWidget(root)
        outer = QtWidgets.QVBoxLayout(root)
        outer.setContentsMargins(34, 28, 34, 28)
        outer.setSpacing(20)

        header = QtWidgets.QHBoxLayout()
        brand = QtWidgets.QVBoxLayout()
        brand.setSpacing(2)
        title = QtWidgets.QLabel("EmbossForge")
        title.setObjectName("brand")
        subtitle = QtWidgets.QLabel("Turn artwork into matched 3D-printable embossing dies.")
        subtitle.setObjectName("muted")
        brand.addWidget(title)
        brand.addWidget(subtitle)
        header.addLayout(brand)
        header.addStretch()
        self.status_pill = QtWidgets.QLabel("READY")
        self.status_pill.setObjectName("statusPill")
        header.addWidget(self.status_pill, 0, QtCore.Qt.AlignmentFlag.AlignTop)
        outer.addLayout(header)

        body = QtWidgets.QHBoxLayout()
        body.setSpacing(22)
        outer.addLayout(body, 1)

        left = QtWidgets.QVBoxLayout()
        left.setSpacing(14)
        body.addLayout(left, 5)

        self.drop = ArtworkDropCard()
        self.drop.fileSelected.connect(self._set_artwork)
        left.addWidget(self.drop)

        preview_card = QtWidgets.QFrame()
        preview_card.setObjectName("card")
        preview_layout = QtWidgets.QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(18, 18, 18, 18)
        preview_heading = QtWidgets.QLabel("DESIGN PREVIEW")
        preview_heading.setObjectName("eyebrow")
        self.preview = QtWidgets.QLabel("Your design will appear here")
        self.preview.setObjectName("preview")
        self.preview.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(260)
        preview_layout.addWidget(preview_heading)
        preview_layout.addWidget(self.preview, 1)
        left.addWidget(preview_card, 1)

        right_card = QtWidgets.QFrame()
        right_card.setObjectName("card")
        right_card.setFixedWidth(360)
        body.addWidget(right_card)
        panel = QtWidgets.QVBoxLayout(right_card)
        panel.setContentsMargins(22, 22, 22, 22)
        panel.setSpacing(13)

        settings_title = QtWidgets.QLabel("Die setup")
        settings_title.setObjectName("sectionTitle")
        panel.addWidget(settings_title)

        self.design_name = QtWidgets.QLineEdit()
        self.design_name.setPlaceholderText("Design name")
        panel.addWidget(self._field("NAME", self.design_name))

        self.diameter = QtWidgets.QDoubleSpinBox()
        self.diameter.setRange(10.0, 180.0)
        self.diameter.setValue(42.0)
        self.diameter.setSuffix(" mm")
        self.diameter.setDecimals(1)
        panel.addWidget(self._field("DIE DIAMETER", self.diameter))

        self.paper = QtWidgets.QComboBox()
        self.paper.addItem("Copy paper  ·  0.10 mm", "copy")
        self.paper.addItem("Premium paper  ·  0.13 mm", "premium")
        self.paper.addItem("Cardstock  ·  0.25 mm", "cardstock")
        self.paper.addItem("Custom thickness", "custom")
        self.paper.currentIndexChanged.connect(self._paper_changed)
        panel.addWidget(self._field("PAPER", self.paper))

        self.custom_paper = QtWidgets.QDoubleSpinBox()
        self.custom_paper.setRange(0.05, 1.50)
        self.custom_paper.setValue(0.10)
        self.custom_paper.setSingleStep(0.01)
        self.custom_paper.setDecimals(2)
        self.custom_paper.setSuffix(" mm")
        self.custom_paper_field = self._field("CUSTOM THICKNESS", self.custom_paper)
        self.custom_paper_field.hide()
        panel.addWidget(self.custom_paper_field)

        self.printer = QtWidgets.QComboBox()
        self.printer.addItem("FlashForge Adventurer 5M · 0.4 mm", "ad5m")
        self.printer.addItem("Generic printer · no size validation", "generic")
        panel.addWidget(self._field("PRINTER", self.printer))

        self.advanced = QtWidgets.QGroupBox("Advanced settings")
        self.advanced.setCheckable(True)
        self.advanced.setChecked(False)
        advanced_layout = QtWidgets.QFormLayout(self.advanced)
        advanced_layout.setContentsMargins(14, 14, 14, 14)

        self.base = QtWidgets.QDoubleSpinBox()
        self.base.setRange(1.0, 12.0)
        self.base.setValue(3.0)
        self.base.setSuffix(" mm")
        self.relief = QtWidgets.QDoubleSpinBox()
        self.relief.setRange(0.20, 2.00)
        self.relief.setValue(0.65)
        self.relief.setSingleStep(0.05)
        self.relief.setSuffix(" mm")
        self.margin = QtWidgets.QDoubleSpinBox()
        self.margin.setRange(0.5, 20.0)
        self.margin.setValue(3.0)
        self.margin.setSuffix(" mm")
        self.clearance = QtWidgets.QDoubleSpinBox()
        self.clearance.setRange(0.0, 1.0)
        self.clearance.setValue(0.20)
        self.clearance.setSingleStep(0.05)
        self.clearance.setSuffix(" mm")
        self.use_profile_clearance = QtWidgets.QCheckBox("Use printer recommendation")
        self.use_profile_clearance.setChecked(True)
        self.invert = QtWidgets.QCheckBox("Invert light-on-dark artwork")

        advanced_layout.addRow("Base", self.base)
        advanced_layout.addRow("Relief", self.relief)
        advanced_layout.addRow("Margin", self.margin)
        advanced_layout.addRow("Clearance", self.clearance)
        advanced_layout.addRow("", self.use_profile_clearance)
        advanced_layout.addRow("", self.invert)
        panel.addWidget(self.advanced)

        output_row = QtWidgets.QHBoxLayout()
        self.output_path = QtWidgets.QLineEdit(str(_default_output_root()))
        self.output_path.setReadOnly(True)
        browse_output = QtWidgets.QPushButton("…")
        browse_output.setObjectName("secondaryButton")
        browse_output.setFixedWidth(42)
        browse_output.clicked.connect(self._choose_output)
        output_row.addWidget(self.output_path)
        output_row.addWidget(browse_output)
        output_wrapper = QtWidgets.QWidget()
        output_wrapper.setLayout(output_row)
        panel.addWidget(self._field("OUTPUT FOLDER", output_wrapper))

        panel.addStretch()
        self.message = QtWidgets.QLabel("Choose a design to begin.")
        self.message.setObjectName("message")
        self.message.setWordWrap(True)
        panel.addWidget(self.message)

        self.generate_button = QtWidgets.QPushButton("Generate die files")
        self.generate_button.setObjectName("primaryButton")
        self.generate_button.setMinimumHeight(48)
        self.generate_button.setEnabled(False)
        self.generate_button.clicked.connect(self._generate)
        panel.addWidget(self.generate_button)

        self.open_folder_button = QtWidgets.QPushButton("Open output folder")
        self.open_folder_button.setObjectName("secondaryButton")
        self.open_folder_button.setMinimumHeight(42)
        self.open_folder_button.hide()
        self.open_folder_button.clicked.connect(self._open_output)
        panel.addWidget(self.open_folder_button)

        footer = QtWidgets.QLabel("STL + OpenSCAD source + manifest  ·  dimensions in millimetres")
        footer.setObjectName("muted")
        outer.addWidget(footer)

    def _field(self, label: str, widget: QtWidgets.QWidget) -> QtWidgets.QWidget:
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        text = QtWidgets.QLabel(label)
        text.setObjectName("eyebrow")
        layout.addWidget(text)
        layout.addWidget(widget)
        return container

    def _set_artwork(self, filename: str) -> None:
        path = Path(filename)
        if not _is_supported(path):
            QtWidgets.QMessageBox.warning(self, "Unsupported design", "Choose an SVG, PNG, JPG, BMP, TIFF or WEBP file.")
            return
        self.artwork_path = path
        self.design_name.setText(path.stem)
        self.drop.show_file(path)
        self._render_preview(path)
        self.generate_button.setEnabled(True)
        self.message.setText("Ready to generate a matched male/female die pair.")
        self.status_pill.setText("READY")
        self.open_folder_button.hide()

    def _render_preview(self, path: Path) -> None:
        target = QtCore.QSize(440, 250)
        if path.suffix.lower() == ".svg":
            renderer = QtSvg.QSvgRenderer(str(path))
            image = QtGui.QImage(target, QtGui.QImage.Format.Format_ARGB32_Premultiplied)
            image.fill(QtCore.Qt.GlobalColor.transparent)
            painter = QtGui.QPainter(image)
            renderer.render(painter)
            painter.end()
            pixmap = QtGui.QPixmap.fromImage(image)
        else:
            pixmap = QtGui.QPixmap(str(path))
        if pixmap.isNull():
            self.preview.setText("Preview unavailable — the generator may still be able to read this file.")
            self.preview.setPixmap(QtGui.QPixmap())
            return
        self.preview.setText("")
        self.preview.setPixmap(
            pixmap.scaled(
                target,
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _paper_changed(self) -> None:
        self.custom_paper_field.setVisible(self.paper.currentData() == "custom")

    def _choose_output(self) -> None:
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Choose output folder", self.output_path.text())
        if folder:
            self.output_path.setText(folder)

    def _request(self) -> DieGenerationRequest:
        assert self.artwork_path is not None
        paper_key = self.paper.currentData()
        custom_thickness = self.custom_paper.value() if paper_key == "custom" else None
        preset = None if paper_key == "custom" else str(paper_key)
        profile = adventurer_5m_profile() if self.printer.currentData() == "ad5m" else None
        clearance = None if (profile is not None and self.use_profile_clearance.isChecked()) else self.clearance.value()
        return DieGenerationRequest(
            artwork=self.artwork_path,
            output_root=Path(self.output_path.text()),
            name=self.design_name.text().strip() or self.artwork_path.stem,
            diameter_mm=self.diameter.value(),
            base_thickness_mm=self.base.value(),
            relief_height_mm=self.relief.value(),
            clearance_mm=clearance,
            paper_preset=preset,
            paper_thickness_mm=custom_thickness,
            margin_mm=self.margin.value(),
            invert=self.invert.isChecked(),
            render_stl=True,
            printer_profile=profile,
        )

    def _generate(self) -> None:
        if self.artwork_path is None:
            return
        self.generate_button.setEnabled(False)
        self.open_folder_button.hide()
        self.status_pill.setText("GENERATING")
        self.message.setText("Normalizing artwork and generating both dies…")
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        self.worker = GenerateThread(self._request(), self)
        self.worker.completed.connect(self._generated)
        self.worker.failed.connect(self._failed)
        self.worker.finished.connect(lambda: QtWidgets.QApplication.restoreOverrideCursor())
        self.worker.start()

    def _generated(self, result) -> None:
        self.result = result
        self.status_pill.setText("DONE")
        self.generate_button.setEnabled(True)
        self.open_folder_button.show()
        male = result.male_stl.name if result.male_stl else "SCAD only"
        female = result.female_stl.name if result.female_stl else "SCAD only"
        self.message.setText(
            f"Done. Generated {male} and {female}.\n"
            f"Paper: {result.spec.paper_thickness_mm:.2f} mm  ·  clearance: {result.spec.female_xy_clearance_mm:.2f} mm"
        )

    def _failed(self, message: str) -> None:
        self.status_pill.setText("ERROR")
        self.generate_button.setEnabled(True)
        self.message.setText(message)
        QtWidgets.QMessageBox.critical(self, "Could not generate dies", message)

    def _open_output(self) -> None:
        path = self.result.output_dir if self.result is not None else Path(self.output_path.text())
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(path.resolve())))

    def dragEnterEvent(self, event):  # noqa: N802
        urls = event.mimeData().urls()
        if urls and _is_supported(Path(urls[0].toLocalFile())):
            event.acceptProposedAction()

    def dropEvent(self, event):  # noqa: N802
        urls = event.mimeData().urls()
        if urls:
            self._set_artwork(urls[0].toLocalFile())
            event.acceptProposedAction()

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #0b0e13; color: #e9eef6; font-family: "Segoe UI", Arial; font-size: 13px; }
            QLabel#brand { font-size: 27px; font-weight: 700; letter-spacing: 0.4px; color: #f7f9fc; }
            QLabel#muted { color: #7f8a9d; }
            QLabel#eyebrow { color: #77849a; font-size: 10px; font-weight: 700; letter-spacing: 1.2px; }
            QLabel#dropTitle { color: #edf4ff; font-size: 17px; font-weight: 600; }
            QLabel#sectionTitle { color: #f4f7fb; font-size: 18px; font-weight: 650; }
            QLabel#statusPill { background: #152033; color: #79a8ff; border: 1px solid #253b60; border-radius: 11px; padding: 5px 10px; font-size: 10px; font-weight: 700; }
            QLabel#message { color: #a9b4c5; padding: 2px; }
            QLabel#preview { color: #667286; background: #080b10; border-radius: 9px; }
            QFrame#card { background: #11161e; border: 1px solid #1e2734; border-radius: 13px; }
            QFrame#dropCard { background: #0e141d; border: 1px dashed #34445c; border-radius: 13px; }
            QFrame#dropCard:hover { border: 1px dashed #6a9cff; background: #101824; }
            QLineEdit, QDoubleSpinBox, QComboBox { background: #0a0f16; color: #e5ebf5; border: 1px solid #263140; border-radius: 8px; padding: 8px 10px; min-height: 20px; }
            QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus { border: 1px solid #5b8ff9; }
            QComboBox QAbstractItemView { background: #11161e; color: #e5ebf5; selection-background-color: #203a67; border: 1px solid #263140; }
            QGroupBox { border: 1px solid #263140; border-radius: 9px; margin-top: 8px; padding-top: 10px; color: #9aa7ba; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QCheckBox { color: #aab5c6; spacing: 8px; }
            QPushButton#primaryButton { background: #5b8ff9; color: #07101f; border: none; border-radius: 9px; font-weight: 700; padding: 10px 14px; }
            QPushButton#primaryButton:hover { background: #73a1ff; }
            QPushButton#primaryButton:disabled { background: #273143; color: #687487; }
            QPushButton#secondaryButton { background: #151c26; color: #c7d0de; border: 1px solid #2a3545; border-radius: 8px; padding: 8px 12px; }
            QPushButton#secondaryButton:hover { border: 1px solid #4c6385; background: #192230; }
            QScrollBar:vertical { background: #0b0e13; width: 8px; }
            QScrollBar::handle:vertical { background: #263140; border-radius: 4px; min-height: 22px; }
            """
        )


def _default_output_root() -> Path:
    documents = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.StandardLocation.DocumentsLocation)
    root = Path(documents) if documents else Path.home()
    return root / "EmbossForge"


def main() -> int:
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    app.setApplicationName("EmbossForge")
    app.setOrganizationName("EmbossForge")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
