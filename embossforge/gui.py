from __future__ import annotations

from dataclasses import replace
import sys
from pathlib import Path

from .config import adventurer_5m_profile
from .generator import DieGenerationRequest, generate_die
from .relief import ArtworkMode, ReliefPolarity, ReliefSpec, ReliefStyle, SourceInterpretation


SUPPORTED_FILTER = "Design files (*.svg *.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp)"
SUPPORTED_SUFFIXES = {".svg", ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


def _qt():
    try:
        from PySide6 import QtCore, QtGui, QtSvg, QtWidgets
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError('PySide6 is required for the desktop app. Install with: pip install -e ".[gui]"') from exc
    return QtCore, QtGui, QtSvg, QtWidgets


QtCore, QtGui, QtSvg, QtWidgets = _qt()


class GenerateThread(QtCore.QThread):
    completed = QtCore.Signal(object)
    failed = QtCore.Signal(str)

    def __init__(self, request: DieGenerationRequest, parent=None):
        super().__init__(parent)
        self.request = request

    def run(self) -> None:  # pragma: no cover
        try:
            result = generate_die(self.request)
        except Exception as exc:
            self.failed.emit(str(exc))
        else:
            self.completed.emit(result)


def _is_supported(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_SUFFIXES


class ArtworkCanvas(QtWidgets.QFrame):
    fileSelected = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("artworkCanvas")
        self.setAcceptDrops(True)
        self.setMinimumHeight(430)
        self._pixmap = QtGui.QPixmap()

        self.stack = QtWidgets.QStackedLayout(self)
        self.stack.setContentsMargins(18, 18, 18, 18)

        empty = QtWidgets.QWidget()
        empty_layout = QtWidgets.QVBoxLayout(empty)
        empty_layout.setContentsMargins(44, 44, 44, 44)
        empty_layout.setSpacing(12)
        empty_layout.addStretch()

        glyph = QtWidgets.QLabel("+")
        glyph.setObjectName("uploadGlyph")
        glyph.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        glyph.setFixedSize(56, 56)

        title = QtWidgets.QLabel("Choose your artwork")
        title.setObjectName("emptyTitle")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        copy = QtWidgets.QLabel("Drop a design here, or browse from your computer.")
        copy.setObjectName("emptyCopy")
        copy.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        copy.setWordWrap(True)

        self.choose_button = QtWidgets.QPushButton("Choose artwork")
        self.choose_button.setObjectName("primaryButton")
        self.choose_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.choose_button.setFixedWidth(180)
        self.choose_button.clicked.connect(self._browse)

        formats = QtWidgets.QLabel("SVG · PNG · JPG · WEBP · TIFF")
        formats.setObjectName("previewHint")
        formats.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        empty_layout.addWidget(glyph, 0, QtCore.Qt.AlignmentFlag.AlignHCenter)
        empty_layout.addWidget(title)
        empty_layout.addWidget(copy)
        empty_layout.addSpacing(6)
        empty_layout.addWidget(self.choose_button, 0, QtCore.Qt.AlignmentFlag.AlignHCenter)
        empty_layout.addWidget(formats)
        empty_layout.addStretch()

        self.preview = QtWidgets.QLabel()
        self.preview.setObjectName("artworkPreview")
        self.preview.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(320, 320)

        self.stack.addWidget(empty)
        self.stack.addWidget(self.preview)
        self.stack.setCurrentIndex(0)

    def _browse(self) -> None:
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Choose artwork", "", SUPPORTED_FILTER)
        if filename:
            self.fileSelected.emit(filename)

    def browse(self) -> None:
        self._browse()

    def clear_preview(self) -> None:
        self._pixmap = QtGui.QPixmap()
        self.preview.clear()
        self.stack.setCurrentIndex(0)

    def set_preview(self, pixmap: QtGui.QPixmap) -> None:
        self._pixmap = pixmap
        self.stack.setCurrentIndex(1)
        self._fit_pixmap()

    def _fit_pixmap(self) -> None:
        if self._pixmap.isNull():
            return
        target = self.preview.size() - QtCore.QSize(48, 48)
        target.setWidth(max(220, target.width()))
        target.setHeight(max(220, target.height()))
        self.preview.setPixmap(
            self._pixmap.scaled(
                target,
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
        )

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._fit_pixmap()

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


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.artwork_path: Path | None = None
        self.result = None
        self.worker: GenerateThread | None = None
        self._last_request: DieGenerationRequest | None = None

        self.setWindowTitle("EmbossForge")
        self.resize(1280, 820)
        self.setMinimumSize(1040, 700)
        self.setAcceptDrops(True)
        self._build_ui()
        self._apply_style()

    def _build_ui(self) -> None:
        root = QtWidgets.QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)

        outer = QtWidgets.QVBoxLayout(root)
        outer.setContentsMargins(30, 24, 30, 26)
        outer.setSpacing(20)

        header = QtWidgets.QHBoxLayout()
        brand = QtWidgets.QVBoxLayout()
        brand.setSpacing(2)
        title = QtWidgets.QLabel("EmbossForge")
        title.setObjectName("brand")
        subtitle = QtWidgets.QLabel("Turn artwork into printer-aware matched embossing dies.")
        subtitle.setObjectName("muted")
        brand.addWidget(title)
        brand.addWidget(subtitle)
        header.addLayout(brand)
        header.addStretch()
        badge = QtWidgets.QLabel("DESKTOP")
        badge.setObjectName("badge")
        header.addWidget(badge, 0, QtCore.Qt.AlignmentFlag.AlignTop)
        outer.addLayout(header)

        body = QtWidgets.QHBoxLayout()
        body.setSpacing(20)
        outer.addLayout(body, 1)
        body.addWidget(self._build_artwork_panel(), 1)
        body.addWidget(self._build_setup_panel(), 0)

    def _build_artwork_panel(self) -> QtWidgets.QWidget:
        card = QtWidgets.QFrame()
        card.setObjectName("card")
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 18)
        layout.setSpacing(14)

        top = QtWidgets.QHBoxLayout()
        headings = QtWidgets.QVBoxLayout()
        headings.setSpacing(2)
        step = QtWidgets.QLabel("1 · ARTWORK")
        step.setObjectName("eyebrow")
        heading = QtWidgets.QLabel("Your design")
        heading.setObjectName("sectionTitle")
        self.file_label = QtWidgets.QLabel("No artwork selected")
        self.file_label.setObjectName("muted")
        headings.addWidget(step)
        headings.addWidget(heading)
        headings.addWidget(self.file_label)
        top.addLayout(headings)
        top.addStretch()

        self.replace_button = QtWidgets.QPushButton("Replace artwork")
        self.replace_button.setObjectName("secondaryButton")
        self.replace_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.replace_button.setFixedHeight(38)
        self.replace_button.hide()
        self.replace_button.clicked.connect(lambda: self.artwork_canvas.browse())
        top.addWidget(self.replace_button, 0, QtCore.Qt.AlignmentFlag.AlignTop)
        layout.addLayout(top)

        self.artwork_canvas = ArtworkCanvas()
        self.artwork_canvas.fileSelected.connect(self._set_artwork)
        layout.addWidget(self.artwork_canvas, 1)

        self.preview_note = QtWidgets.QLabel(
            "Simple emboss uses the design shape. Variable depth uses a true grayscale height map where tone means physical Z height."
        )
        self.preview_note.setObjectName("previewHint")
        self.preview_note.setWordWrap(True)
        layout.addWidget(self.preview_note)
        return card

    def _build_setup_panel(self) -> QtWidgets.QWidget:
        card = QtWidgets.QFrame()
        card.setObjectName("card")
        card.setMinimumWidth(430)
        card.setMaximumWidth(500)

        panel = QtWidgets.QVBoxLayout(card)
        panel.setContentsMargins(18, 18, 18, 18)
        panel.setSpacing(14)
        title = QtWidgets.QLabel("Create your die pair")
        title.setObjectName("sectionTitle")
        copy = QtWidgets.QLabel("Choose the style first. EmbossForge keeps the male and female printer-compatible as one pair.")
        copy.setObjectName("muted")
        copy.setWordWrap(True)
        panel.addWidget(title)
        panel.addWidget(copy)

        scroll = QtWidgets.QScrollArea()
        scroll.setObjectName("settingsScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

        settings = QtWidgets.QWidget()
        settings.setObjectName("settingsBody")
        settings_layout = QtWidgets.QVBoxLayout(settings)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(12)
        settings_layout.addWidget(self._build_style_settings())
        settings_layout.addWidget(self._build_die_settings())
        settings_layout.addWidget(self._build_printer_settings())
        settings_layout.addWidget(self._build_advanced_settings())
        settings_layout.addWidget(self._build_output_settings())
        settings_layout.addStretch()
        scroll.setWidget(settings)
        panel.addWidget(scroll, 1)

        separator = QtWidgets.QFrame()
        separator.setObjectName("separator")
        separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        panel.addWidget(separator)

        self.validation_message = QtWidgets.QLabel("Pair fit validation will run before files are accepted.")
        self.validation_message.setObjectName("validationMessage")
        self.validation_message.setWordWrap(True)
        panel.addWidget(self.validation_message)

        self.message = QtWidgets.QLabel("Choose artwork to get started.")
        self.message.setObjectName("statusMessage")
        self.message.setWordWrap(True)
        panel.addWidget(self.message)

        self.generate_button = QtWidgets.QPushButton("Generate matched die pair")
        self.generate_button.setObjectName("primaryButton")
        self.generate_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.generate_button.setMinimumHeight(50)
        self.generate_button.setEnabled(False)
        self.generate_button.clicked.connect(self._generate)
        panel.addWidget(self.generate_button)

        self.open_folder_button = QtWidgets.QPushButton("Open generated files")
        self.open_folder_button.setObjectName("secondaryButton")
        self.open_folder_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.open_folder_button.setMinimumHeight(42)
        self.open_folder_button.hide()
        self.open_folder_button.clicked.connect(self._open_output)
        panel.addWidget(self.open_folder_button)
        return card

    def _build_style_settings(self) -> QtWidgets.QWidget:
        section = self._section_card("2 · EMBOSS STYLE", "How should depth work?")
        layout = section.layout()

        self.emboss_style = QtWidgets.QComboBox()
        self.emboss_style.addItem("Simple emboss — one height", ArtworkMode.BINARY.value)
        self.emboss_style.addItem("Variable depth — grayscale controls height", ArtworkMode.RELIEF.value)
        self._prepare_input(self.emboss_style)
        self.emboss_style.currentIndexChanged.connect(self._style_changed)
        layout.addWidget(
            self._field(
                "Emboss style",
                self.emboss_style,
                "Simple is best for logos and line art. Variable depth is for real height maps.",
            )
        )

        self.relief_panel = QtWidgets.QFrame()
        self.relief_panel.setObjectName("reliefCard")
        relief_layout = QtWidgets.QVBoxLayout(self.relief_panel)
        relief_layout.setContentsMargins(12, 12, 12, 12)
        relief_layout.setSpacing(10)

        self.source_interpretation = QtWidgets.QComboBox()
        self.source_interpretation.addItem("True height map — grayscale is exact depth", SourceInterpretation.HEIGHT_MAP.value)
        self.source_interpretation.addItem("3D-looking / shaded reference", SourceInterpretation.SHADED_REFERENCE.value)
        self._prepare_input(self.source_interpretation)
        self.source_interpretation.currentIndexChanged.connect(self._source_changed)
        relief_layout.addWidget(self._field("Image meaning", self.source_interpretation))

        self.source_help = QtWidgets.QLabel(
            "Use a true height map only when white means zero relief and dark tones intentionally mean higher relief."
        )
        self.source_help.setObjectName("fieldHint")
        self.source_help.setWordWrap(True)
        relief_layout.addWidget(self.source_help)

        self.relief_max = QtWidgets.QDoubleSpinBox()
        self.relief_max.setRange(0.10, 2.00)
        self.relief_max.setValue(0.65)
        self.relief_max.setSingleStep(0.05)
        self.relief_max.setSuffix(" mm")
        self.relief_max.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._prepare_input(self.relief_max)
        relief_layout.addWidget(self._field("Maximum relief", self.relief_max))

        self.relief_style = QtWidgets.QComboBox()
        self.relief_style.addItem("Stepped — FDM friendly", ReliefStyle.STEPPED.value)
        self.relief_style.addItem("Continuous — smooth height field", ReliefStyle.CONTINUOUS.value)
        self._prepare_input(self.relief_style)
        self.relief_style.currentIndexChanged.connect(self._relief_style_changed)
        relief_layout.addWidget(self._field("Depth style", self.relief_style))

        self.relief_levels = QtWidgets.QSpinBox()
        self.relief_levels.setRange(2, 32)
        self.relief_levels.setValue(6)
        self.relief_levels.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._prepare_input(self.relief_levels)
        self.relief_levels_field = self._field("Height levels", self.relief_levels, "Six levels is the current FDM-oriented default.")
        relief_layout.addWidget(self.relief_levels_field)

        self.relief_polarity = QtWidgets.QComboBox()
        self.relief_polarity.addItem("Darker = higher relief", ReliefPolarity.DARK_HIGH.value)
        self.relief_polarity.addItem("Lighter = higher relief", ReliefPolarity.LIGHT_HIGH.value)
        self._prepare_input(self.relief_polarity)
        relief_layout.addWidget(self._field("Tone direction", self.relief_polarity))

        self.relief_panel.hide()
        layout.addWidget(self.relief_panel)
        return section

    def _build_die_settings(self) -> QtWidgets.QWidget:
        section = self._section_card("3 · DIE", "Size and paper")
        layout = section.layout()

        self.design_name = QtWidgets.QLineEdit()
        self.design_name.setPlaceholderText("e.g. library-seal")
        self._prepare_input(self.design_name)
        layout.addWidget(self._field("Design name", self.design_name))

        self.diameter = QtWidgets.QDoubleSpinBox()
        self.diameter.setRange(10.0, 180.0)
        self.diameter.setValue(42.0)
        self.diameter.setSuffix(" mm")
        self.diameter.setDecimals(1)
        self.diameter.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._prepare_input(self.diameter)
        layout.addWidget(self._field("Die diameter", self.diameter, "42 mm is a useful general-purpose starting size."))

        self.paper = QtWidgets.QComboBox()
        self.paper.addItem("Copy paper — 0.10 mm", "copy")
        self.paper.addItem("Premium paper — 0.13 mm", "premium")
        self.paper.addItem("Cardstock — 0.25 mm", "cardstock")
        self.paper.addItem("Custom thickness", "custom")
        self.paper.currentIndexChanged.connect(self._paper_changed)
        self._prepare_input(self.paper)
        layout.addWidget(self._field("Paper type", self.paper, "Paper thickness is part of the mating clearance calculation."))

        self.custom_paper = QtWidgets.QDoubleSpinBox()
        self.custom_paper.setRange(0.05, 1.50)
        self.custom_paper.setValue(0.10)
        self.custom_paper.setSingleStep(0.01)
        self.custom_paper.setDecimals(2)
        self.custom_paper.setSuffix(" mm")
        self.custom_paper.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._prepare_input(self.custom_paper)
        self.custom_paper_field = self._field("Paper thickness", self.custom_paper)
        self.custom_paper_field.hide()
        layout.addWidget(self.custom_paper_field)
        return section

    def _build_printer_settings(self) -> QtWidgets.QWidget:
        section = self._section_card("4 · PRINTER", "Printability profile")
        layout = section.layout()
        self.printer = QtWidgets.QComboBox()
        self.printer.addItem("FlashForge Adventurer 5M — 0.4 mm nozzle", "ad5m")
        self.printer.addItem("Generic FDM — geometry only", "generic")
        self._prepare_input(self.printer)
        layout.addWidget(
            self._field(
                "Printer",
                self.printer,
                "The selected nozzle/profile is used for positive/negative feature checks and clearance defaults.",
            )
        )
        return section

    def _build_advanced_settings(self) -> QtWidgets.QWidget:
        wrapper = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.advanced_toggle = QtWidgets.QToolButton()
        self.advanced_toggle.setObjectName("advancedToggle")
        self.advanced_toggle.setText("›  Advanced settings")
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.advanced_toggle.toggled.connect(self._advanced_toggled)
        layout.addWidget(self.advanced_toggle)

        self.advanced_panel = QtWidgets.QFrame()
        self.advanced_panel.setObjectName("innerCard")
        advanced = QtWidgets.QVBoxLayout(self.advanced_panel)
        advanced.setContentsMargins(14, 14, 14, 14)
        advanced.setSpacing(12)

        self.base = QtWidgets.QDoubleSpinBox()
        self.base.setRange(1.0, 12.0)
        self.base.setValue(3.0)
        self.base.setSuffix(" mm")
        self.base.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._prepare_input(self.base)
        advanced.addWidget(self._field("Base thickness", self.base))

        self.binary_relief = QtWidgets.QDoubleSpinBox()
        self.binary_relief.setRange(0.20, 2.00)
        self.binary_relief.setValue(0.65)
        self.binary_relief.setSingleStep(0.05)
        self.binary_relief.setSuffix(" mm")
        self.binary_relief.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._prepare_input(self.binary_relief)
        self.binary_relief_field = self._field("Simple emboss height", self.binary_relief)
        advanced.addWidget(self.binary_relief_field)

        self.margin = QtWidgets.QDoubleSpinBox()
        self.margin.setRange(0.5, 20.0)
        self.margin.setValue(3.0)
        self.margin.setSuffix(" mm")
        self.margin.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._prepare_input(self.margin)
        advanced.addWidget(self._field("Artwork margin", self.margin))

        self.use_profile_clearance = QtWidgets.QCheckBox("Use printer-recommended clearance")
        self.use_profile_clearance.setChecked(True)
        self.use_profile_clearance.toggled.connect(self._profile_clearance_toggled)
        advanced.addWidget(self.use_profile_clearance)

        self.clearance = QtWidgets.QDoubleSpinBox()
        self.clearance.setRange(0.0, 1.0)
        self.clearance.setValue(0.20)
        self.clearance.setSingleStep(0.05)
        self.clearance.setSuffix(" mm")
        self.clearance.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._prepare_input(self.clearance)
        self.clearance.setEnabled(False)
        advanced.addWidget(self._field("Manual clearance", self.clearance))

        self.invert = QtWidgets.QCheckBox("Invert light-on-dark artwork (simple mode)")
        advanced.addWidget(self.invert)

        self.relief_advanced = QtWidgets.QFrame()
        self.relief_advanced.setObjectName("reliefAdvanced")
        relief_adv = QtWidgets.QVBoxLayout(self.relief_advanced)
        relief_adv.setContentsMargins(0, 6, 0, 0)
        relief_adv.setSpacing(10)

        self.relief_gamma = QtWidgets.QDoubleSpinBox()
        self.relief_gamma.setRange(0.10, 4.00)
        self.relief_gamma.setValue(1.0)
        self.relief_gamma.setSingleStep(0.1)
        self.relief_gamma.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._prepare_input(self.relief_gamma)
        relief_adv.addWidget(self._field("Relief gamma", self.relief_gamma))

        self.relief_zero = QtWidgets.QDoubleSpinBox()
        self.relief_zero.setRange(0.0, 0.25)
        self.relief_zero.setValue(0.02)
        self.relief_zero.setSingleStep(0.01)
        self.relief_zero.setDecimals(2)
        self.relief_zero.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._prepare_input(self.relief_zero)
        relief_adv.addWidget(self._field("Background dead zone", self.relief_zero))

        self.relief_smoothing = QtWidgets.QDoubleSpinBox()
        self.relief_smoothing.setRange(0.0, 2.0)
        self.relief_smoothing.setValue(0.0)
        self.relief_smoothing.setSingleStep(0.05)
        self.relief_smoothing.setSuffix(" mm")
        self.relief_smoothing.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._prepare_input(self.relief_smoothing)
        relief_adv.addWidget(self._field("Relief smoothing", self.relief_smoothing))

        self.relief_quality = QtWidgets.QComboBox()
        self.relief_quality.addItem("Balanced", "balanced")
        self.relief_quality.addItem("Draft / faster", "draft")
        self.relief_quality.addItem("Fine / denser mesh", "fine")
        self._prepare_input(self.relief_quality)
        relief_adv.addWidget(self._field("Height-map quality", self.relief_quality))

        self.auto_filter = QtWidgets.QCheckBox("Filter sub-resolution relief before deriving both dies")
        self.auto_filter.setChecked(True)
        relief_adv.addWidget(self.auto_filter)
        self.relief_advanced.hide()
        advanced.addWidget(self.relief_advanced)

        note = QtWidgets.QLabel("Matched-pair interference is never bypassed. Paper-risk warnings can be accepted explicitly if intentional.")
        note.setObjectName("fieldHint")
        note.setWordWrap(True)
        advanced.addWidget(note)

        self.advanced_panel.hide()
        layout.addWidget(self.advanced_panel)
        return wrapper

    def _build_output_settings(self) -> QtWidgets.QWidget:
        section = self._section_card("5 · EXPORT", "Where to save")
        layout = section.layout()
        self.output_path = QtWidgets.QLineEdit(str(_default_output_root()))
        self.output_path.setReadOnly(True)
        self._prepare_input(self.output_path)

        change = QtWidgets.QPushButton("Change")
        change.setObjectName("secondaryButton")
        change.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        change.setFixedHeight(42)
        change.setFixedWidth(82)
        change.clicked.connect(self._choose_output)

        row = QtWidgets.QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self.output_path, 1)
        row.addWidget(change)
        field = QtWidgets.QWidget()
        field_layout = QtWidgets.QVBoxLayout(field)
        field_layout.setContentsMargins(0, 0, 0, 0)
        label = QtWidgets.QLabel("Save folder")
        label.setObjectName("fieldLabel")
        field_layout.addWidget(label)
        field_layout.addLayout(row)
        layout.addWidget(field)
        return section

    def _section_card(self, eyebrow: str, title: str) -> QtWidgets.QFrame:
        card = QtWidgets.QFrame()
        card.setObjectName("innerCard")
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        eye = QtWidgets.QLabel(eyebrow)
        eye.setObjectName("eyebrow")
        heading = QtWidgets.QLabel(title)
        heading.setObjectName("subsectionTitle")
        layout.addWidget(eye)
        layout.addWidget(heading)
        return card

    def _field(self, label: str, widget: QtWidgets.QWidget, helper: str | None = None) -> QtWidgets.QWidget:
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        text = QtWidgets.QLabel(label)
        text.setObjectName("fieldLabel")
        layout.addWidget(text)
        layout.addWidget(widget)
        if helper:
            hint = QtWidgets.QLabel(helper)
            hint.setObjectName("fieldHint")
            hint.setWordWrap(True)
            layout.addWidget(hint)
        return container

    @staticmethod
    def _prepare_input(widget: QtWidgets.QWidget) -> None:
        widget.setMinimumHeight(42)
        widget.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)

    def _style_changed(self) -> None:
        relief = self.emboss_style.currentData() == ArtworkMode.RELIEF.value
        self.relief_panel.setVisible(relief)
        self.binary_relief_field.setVisible(not relief)
        self.relief_advanced.setVisible(relief and self.advanced_toggle.isChecked())
        self.invert.setVisible(not relief)
        self.preview_note.setText(
            "Variable depth uses an unlit height map: white = zero relief and darker tones = more relief by default."
            if relief
            else "Simple emboss uses the design shape at one height. Printer-aware filtering keeps both die halves compatible."
        )
        self._source_changed()
        self._update_generate_enabled()

    def _source_changed(self) -> None:
        if self.emboss_style.currentData() != ArtworkMode.RELIEF.value:
            return
        shaded = self.source_interpretation.currentData() == SourceInterpretation.SHADED_REFERENCE.value
        if shaded:
            self.source_help.setText(
                "A shaded/metallic render contains lighting, not literal depth. This build will not guess Z from highlights and shadows; convert it to a true EmbossForge height map first."
            )
            self.source_help.setProperty("state", "warning")
        else:
            self.source_help.setText(
                "True height map: white is the flat die surface and grayscale intentionally encodes physical height."
            )
            self.source_help.setProperty("state", "normal")
        self._refresh_style(self.source_help)
        self._update_generate_enabled()

    def _relief_style_changed(self) -> None:
        self.relief_levels_field.setVisible(self.relief_style.currentData() == ReliefStyle.STEPPED.value)

    def _advanced_toggled(self, checked: bool) -> None:
        self.advanced_panel.setVisible(checked)
        self.advanced_toggle.setText(("⌄" if checked else "›") + "  Advanced settings")
        self.relief_advanced.setVisible(checked and self.emboss_style.currentData() == ArtworkMode.RELIEF.value)

    def _profile_clearance_toggled(self, checked: bool) -> None:
        self.clearance.setEnabled(not checked)

    def _paper_changed(self) -> None:
        self.custom_paper_field.setVisible(self.paper.currentData() == "custom")

    def _set_artwork(self, filename: str) -> None:
        path = Path(filename)
        if not _is_supported(path):
            QtWidgets.QMessageBox.warning(self, "Unsupported artwork", "Choose an SVG, PNG, JPG, BMP, TIFF or WEBP file.")
            return
        self.artwork_path = path
        self.result = None
        self.design_name.setText(path.stem)
        self.file_label.setText(path.name)
        self.replace_button.show()
        self._render_preview(path)
        self.open_folder_button.hide()
        self.message.setText("Artwork loaded. Choose the emboss style and review the settings.")
        self.message.setProperty("state", "ready")
        self.validation_message.setText("Pair fit validation will run using the selected printer/nozzle profile.")
        self._refresh_style(self.message)
        self._update_generate_enabled()

    def _render_preview(self, path: Path) -> None:
        if path.suffix.lower() == ".svg":
            renderer = QtSvg.QSvgRenderer(str(path))
            if not renderer.isValid():
                self.artwork_canvas.clear_preview()
                QtWidgets.QMessageBox.warning(self, "Preview unavailable", "The SVG could not be previewed.")
                return
            image = QtGui.QImage(1000, 760, QtGui.QImage.Format.Format_ARGB32_Premultiplied)
            image.fill(QtGui.QColor("#f6f2e8"))
            painter = QtGui.QPainter(image)
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
            renderer.render(painter, QtCore.QRectF(70, 70, 860, 620))
            painter.end()
            pixmap = QtGui.QPixmap.fromImage(image)
        else:
            source = QtGui.QPixmap(str(path))
            if source.isNull():
                self.artwork_canvas.clear_preview()
                QtWidgets.QMessageBox.warning(self, "Preview unavailable", "The image could not be previewed.")
                return
            canvas = QtGui.QPixmap(max(1000, source.width()), max(760, source.height()))
            canvas.fill(QtGui.QColor("#f6f2e8"))
            painter = QtGui.QPainter(canvas)
            fitted = source.scaled(
                canvas.size() - QtCore.QSize(140, 140),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
            painter.drawPixmap((canvas.width() - fitted.width()) // 2, (canvas.height() - fitted.height()) // 2, fitted)
            painter.end()
            pixmap = canvas
        self.artwork_canvas.set_preview(pixmap)

    def _choose_output(self) -> None:
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Choose save folder", self.output_path.text())
        if folder:
            self.output_path.setText(folder)

    def _update_generate_enabled(self) -> None:
        enabled = self.artwork_path is not None and self.worker is None
        if self.emboss_style.currentData() == ArtworkMode.RELIEF.value:
            enabled = enabled and self.source_interpretation.currentData() == SourceInterpretation.HEIGHT_MAP.value
        self.generate_button.setEnabled(enabled)
        if self.artwork_path is not None and not enabled and self.emboss_style.currentData() == ArtworkMode.RELIEF.value:
            if self.source_interpretation.currentData() == SourceInterpretation.SHADED_REFERENCE.value:
                self.message.setText("Convert this shaded reference to a true height map before generating the die pair.")
                self.message.setProperty("state", "warning")
                self._refresh_style(self.message)

    def _request(self) -> DieGenerationRequest:
        assert self.artwork_path is not None
        paper_key = self.paper.currentData()
        custom_thickness = self.custom_paper.value() if paper_key == "custom" else None
        preset = None if paper_key == "custom" else str(paper_key)
        profile = adventurer_5m_profile() if self.printer.currentData() == "ad5m" else None
        clearance = None if (profile is not None and self.use_profile_clearance.isChecked()) else self.clearance.value()
        mode = ArtworkMode(self.emboss_style.currentData())

        relief_spec = None
        source = SourceInterpretation.FLAT_ARTWORK
        if mode == ArtworkMode.RELIEF:
            source = SourceInterpretation(self.source_interpretation.currentData())
            relief_spec = ReliefSpec(
                max_relief_mm=self.relief_max.value(),
                style=ReliefStyle(self.relief_style.currentData()),
                levels=self.relief_levels.value(),
                gamma=self.relief_gamma.value(),
                polarity=ReliefPolarity(self.relief_polarity.currentData()),
                zero_threshold=self.relief_zero.value(),
                smoothing_mm=self.relief_smoothing.value(),
                sampling_quality=str(self.relief_quality.currentData()),
                auto_filter_subresolution=self.auto_filter.isChecked(),
            )

        return DieGenerationRequest(
            artwork=self.artwork_path,
            output_root=Path(self.output_path.text()),
            name=self.design_name.text().strip() or self.artwork_path.stem,
            diameter_mm=self.diameter.value(),
            base_thickness_mm=self.base.value(),
            relief_height_mm=self.binary_relief.value(),
            clearance_mm=clearance,
            paper_preset=preset,
            paper_thickness_mm=custom_thickness,
            margin_mm=self.margin.value(),
            invert=self.invert.isChecked(),
            render_stl=True,
            printer_profile=profile,
            artwork_mode=mode,
            source_interpretation=source,
            relief=relief_spec,
        )

    def _generate(self) -> None:
        if self.artwork_path is None:
            return
        request = self._request()
        self._start_generation(request)

    def _start_generation(self, request: DieGenerationRequest) -> None:
        self._last_request = request
        self.generate_button.setEnabled(False)
        self.generate_button.setText("Generating…")
        self.open_folder_button.hide()
        self.message.setText("Building and validating both halves. EmbossForge will reject predicted die-to-die interference.")
        self.message.setProperty("state", "working")
        self.validation_message.setText("Running printer-aware pair fit checks…")
        self._refresh_style(self.message)
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        self.worker = GenerateThread(request, self)
        self.worker.completed.connect(self._generated)
        self.worker.failed.connect(self._failed)
        self.worker.finished.connect(self._worker_finished)
        self.worker.start()

    def _worker_finished(self) -> None:
        QtWidgets.QApplication.restoreOverrideCursor()
        self.worker = None
        self._update_generate_enabled()

    def _generated(self, result) -> None:
        self.result = result
        self.generate_button.setText("Generate again")
        self.open_folder_button.show()

        caution_count = sum(1 for f in result.validation.findings if f.severity.value in {"caution", "high"})
        fit_text = "✓ Pair fit checks passed"
        if caution_count:
            fit_text += f" · {caution_count} paper/quality caution(s)"
        if "partial" in result.validation.verification_level:
            fit_text += " · complex artwork coverage is partial"
        self.validation_message.setText(fit_text)
        self.validation_message.setProperty("state", "success" if not caution_count else "warning")
        self._refresh_style(self.validation_message)

        male = result.male_stl.name if result.male_stl else "male SCAD"
        female = result.female_stl.name if result.female_stl else "female SCAD"
        self.message.setText(
            f"✓ Files ready — {male} + {female}. Paper {result.spec.paper_thickness_mm:.2f} mm · "
            f"clearance {result.spec.female_xy_clearance_mm:.2f} mm."
        )
        self.message.setProperty("state", "success")
        self._refresh_style(self.message)

    def _failed(self, message: str) -> None:
        self.generate_button.setText("Try again")
        if "high experimental paper-risk" in message and self._last_request is not None:
            self.message.setText("The geometry can mate, but EmbossForge found a high experimental paper-damage risk.")
            self.message.setProperty("state", "warning")
            self._refresh_style(self.message)
            box = QtWidgets.QMessageBox(self)
            box.setWindowTitle("High paper-risk warning")
            box.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            box.setText("This relief may be harsh on the selected paper.")
            box.setInformativeText(message + "\n\nDie-to-die interference cannot be overridden; this confirmation applies only to paper-risk heuristics.")
            adjust = box.addButton("Go back and adjust", QtWidgets.QMessageBox.ButtonRole.RejectRole)
            generate_anyway = box.addButton("Generate anyway", QtWidgets.QMessageBox.ButtonRole.AcceptRole)
            box.exec()
            if box.clickedButton() is generate_anyway:
                self._start_generation(replace(self._last_request, allow_risky=True))
            else:
                self._update_generate_enabled()
            return

        hard_mating = "closure validation failed" in message.lower() or "mating" in message.lower()
        self.validation_message.setText("✕ Pair fit validation failed" if hard_mating else "Generation validation stopped")
        self.validation_message.setProperty("state", "error")
        self._refresh_style(self.validation_message)
        self.message.setText(f"Could not generate the dies: {message}")
        self.message.setProperty("state", "error")
        self._refresh_style(self.message)
        QtWidgets.QMessageBox.critical(self, "Could not generate dies", message)

    @staticmethod
    def _refresh_style(widget: QtWidgets.QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

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
            QMainWindow, QWidget#root { background: #090d12; color: #eef2f8; font-family: "Segoe UI", Arial, sans-serif; font-size: 13px; }
            QWidget { color: #eef2f8; }
            QLabel#brand { color: #f8fafc; font-size: 28px; font-weight: 700; }
            QLabel#muted { color: #8b98aa; }
            QLabel#badge { background: #121c2c; color: #82aaff; border: 1px solid #253858; border-radius: 11px; padding: 5px 10px; font-size: 10px; font-weight: 700; }
            QFrame#card { background: #10161e; border: 1px solid #202a36; border-radius: 14px; }
            QFrame#innerCard { background: #0c1219; border: 1px solid #1e2936; border-radius: 11px; }
            QFrame#reliefCard { background: #101927; border: 1px solid #284365; border-radius: 9px; }
            QFrame#separator { color: #202a36; background: #202a36; max-height: 1px; border: 0; }
            QLabel#eyebrow { color: #71819a; font-size: 10px; font-weight: 700; }
            QLabel#sectionTitle { color: #f5f7fb; font-size: 19px; font-weight: 650; }
            QLabel#subsectionTitle { color: #e9eef6; font-size: 14px; font-weight: 650; }
            QLabel#fieldLabel { color: #dfe6ef; font-size: 12px; font-weight: 600; }
            QLabel#fieldHint, QLabel#previewHint { color: #75839a; font-size: 11px; }
            QLabel#fieldHint[state="warning"] { color: #e7bd72; }
            QFrame#artworkCanvas { background: #f6f2e8; border: 1px dashed #55657a; border-radius: 12px; }
            QFrame#artworkCanvas:hover { border-color: #78a3ff; }
            QLabel#artworkPreview { background: #f6f2e8; border: 0; }
            QLabel#uploadGlyph { background: #e8e2d5; color: #30415a; border: 1px solid #d5cdbd; border-radius: 28px; font-size: 28px; }
            QLabel#emptyTitle { color: #17202b; font-size: 19px; font-weight: 700; }
            QLabel#emptyCopy { color: #66717e; font-size: 13px; }
            QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox { background: #090e14; color: #edf2f8; border: 1px solid #263342; border-radius: 8px; padding: 7px 11px; selection-background-color: #365fa7; }
            QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus { border-color: #6d9cff; }
            QLineEdit:disabled, QDoubleSpinBox:disabled, QSpinBox:disabled, QComboBox:disabled { color: #69768a; background: #0b1016; border-color: #1c2631; }
            QComboBox::drop-down { border: 0; width: 30px; }
            QComboBox QAbstractItemView { background: #10161e; color: #edf2f8; border: 1px solid #263342; selection-background-color: #24477f; padding: 5px; }
            QCheckBox { color: #bcc6d4; spacing: 8px; }
            QToolButton#advancedToggle { background: transparent; color: #9eabc0; border: 0; text-align: left; padding: 8px 4px; font-weight: 600; }
            QToolButton#advancedToggle:hover { color: #dbe5f4; }
            QPushButton#primaryButton { background: #6d9cff; color: #07101d; border: 0; border-radius: 9px; padding: 10px 16px; font-weight: 700; }
            QPushButton#primaryButton:hover { background: #82aaff; }
            QPushButton#primaryButton:pressed { background: #5d89e4; }
            QPushButton#primaryButton:disabled { background: #263244; color: #69778c; }
            QPushButton#secondaryButton { background: #151d27; color: #c8d3e1; border: 1px solid #2a3748; border-radius: 8px; padding: 8px 12px; font-weight: 600; }
            QPushButton#secondaryButton:hover { background: #1a2532; border-color: #4d6483; }
            QLabel#statusMessage, QLabel#validationMessage { color: #9ba8ba; background: #0c1219; border: 1px solid #1f2a36; border-radius: 8px; padding: 10px 12px; }
            QLabel#statusMessage[state="ready"] { color: #b8c9e6; }
            QLabel#statusMessage[state="working"] { color: #a9c3ff; border-color: #2b4b7c; background: #101a29; }
            QLabel#statusMessage[state="success"], QLabel#validationMessage[state="success"] { color: #b9e7cc; border-color: #28533a; background: #0e1c15; }
            QLabel#statusMessage[state="warning"], QLabel#validationMessage[state="warning"] { color: #f1d39a; border-color: #6b5428; background: #211b0f; }
            QLabel#statusMessage[state="error"], QLabel#validationMessage[state="error"] { color: #ffc1c1; border-color: #6a3232; background: #241212; }
            QScrollArea#settingsScroll, QWidget#settingsBody { background: transparent; border: 0; }
            QScrollBar:vertical { background: transparent; width: 7px; margin: 2px 0 2px 0; }
            QScrollBar::handle:vertical { background: #2a3544; border-radius: 3px; min-height: 28px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
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
    app.setFont(QtGui.QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
