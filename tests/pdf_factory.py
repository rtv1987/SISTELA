"""Synthetic PDFs exercise the byte-to-schedule pipeline, not extraction mocks."""

import pymupdf


def make_pdf(path, pages, grid=True, title="", headers=True, order=None):
    document = pymupdf.open()
    default = ["No", "Description", "Model", "Unit", "Qty", "Notes"]
    order = order or list(range(6))
    widths = {0: 40, 1: 280, 2: 90, 3: 65, 4: 65, 5: 110}
    for data in pages:
        page = document.new_page(width=850, height=900)
        if title:
            page.insert_text((40, 45), title, fontsize=11)
        rows = ([default] if headers else []) + data
        xs = [40]
        for col in order:
            xs.append(xs[-1] + widths[col])
        y = 100
        for row in rows:
            height = max(28, max((v.count("\n") + 1) * 13 + 12 for v in row))
            for col, x in zip(order, xs):
                page.insert_text((x + 4, y + 13), row[col], fontsize=9)
            if grid:
                page.draw_line((xs[0], y), (xs[-1], y))
                for x in xs:
                    page.draw_line((x, y), (x, y + height))
            y += height
        if grid:
            page.draw_line((xs[0], y), (xs[-1], y))
    document.save(path)
    document.close()
    return path


def items(count=5, start=1, work=False):
    return [
        [
            str(i),
            f"Kabelio montavimas {i}" if work else f"Valdymo modulis {i}",
            f"AB-{i}",
            "vnt.",
            str(i * 3),
            "",
        ]
        for i in range(start, start + count)
    ]
