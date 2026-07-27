"""
Tests for preview.annotations.AnnotationLayer / Annotation.
"""

from __future__ import annotations

from preview.annotations import Annotation, AnnotationLayer, AnnotationType


class TestAnnotation:

    def test_bounds_padded_by_stroke_width(self):

        annotation = Annotation(
            AnnotationType.LINE, points=[(0, 0), (10, 10)], stroke_width=4
        )

        bounds = annotation.bounds()

        assert bounds.left < 0

        assert bounds.right > 10

    def test_translate_moves_all_points(self):

        annotation = Annotation(
            AnnotationType.RECTANGLE, points=[(0, 0), (10, 10)]
        )

        annotation.translate(5, 5)

        assert annotation.points == [(5, 5), (15, 15)]

    def test_round_trip_serialization(self):

        annotation = Annotation(
            AnnotationType.TEXT, points=[(1, 2)], text="hi", color="#ABCDEF"
        )

        restored = Annotation.from_dict(annotation.to_dict())

        assert restored.text == "hi"

        assert restored.color == "#ABCDEF"

        assert restored.type == AnnotationType.TEXT

    def test_invalid_opacity_raises(self):

        import pytest

        with pytest.raises(ValueError):
            Annotation(AnnotationType.ARROW, opacity=1.5)


class TestAnnotationLayer:

    def test_add_assigns_increasing_z_index(self):

        layer = AnnotationLayer()

        first = layer.add(Annotation(AnnotationType.ARROW, points=[(0, 0)]))

        second = layer.add(Annotation(AnnotationType.ARROW, points=[(0, 0)]))

        assert second.z_index > first.z_index

    def test_hit_test_finds_topmost(self):

        layer = AnnotationLayer()

        layer.add(
            Annotation(
                AnnotationType.RECTANGLE, points=[(0, 0), (100, 100)]
            )
        )

        top = layer.add(
            Annotation(
                AnnotationType.RECTANGLE, points=[(10, 10), (50, 50)]
            )
        )

        hit = layer.hit_test(20, 20)

        assert hit is top

    def test_undo_redo(self):

        layer = AnnotationLayer()

        layer.add(Annotation(AnnotationType.ARROW, points=[(0, 0), (1, 1)]))

        assert layer.count == 1

        assert layer.undo()

        assert layer.count == 0

        assert layer.redo()

        assert layer.count == 1

    def test_remove(self):

        layer = AnnotationLayer()

        annotation = layer.add(
            Annotation(AnnotationType.ARROW, points=[(0, 0), (1, 1)])
        )

        assert layer.remove(annotation.id)

        assert layer.count == 0

    def test_locked_annotation_excluded_from_hit_test(self):

        layer = AnnotationLayer()

        annotation = layer.add(
            Annotation(
                AnnotationType.RECTANGLE, points=[(0, 0), (100, 100)]
            )
        )

        layer.update(annotation.id, locked=True)

        assert layer.hit_test(50, 50) is None
