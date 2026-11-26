from io import BytesIO

from django.http import FileResponse
from drf_spectacular.utils import extend_schema, OpenApiTypes
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

from .journal import JournalGridView
from .journal_serializers import JournalQuerySerializer


XLSX_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
ATTENDANCE_LABELS = {'present': 'П', 'absent': 'Н', 'late': 'О', 'excused': 'У'}


class JournalExportView(JournalGridView):
    @extend_schema(parameters=[JournalQuerySerializer], responses={(200, XLSX_TYPE): OpenApiTypes.BINARY})
    def get(self, request):
        week = self.week_data(request.query_params)
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = 'Ведомость'
        dates = week['dates']
        sheet.append([
            'Студент', *(day['date'] for day in dates), 'Средний балл', 'Посещаемость %',
        ])
        for header in sheet[1]:
            header.font = Font(bold=True)
        sheet.freeze_panes = 'B2'
        sheet.column_dimensions['A'].width = 32
        for column in range(2, sheet.max_column + 1):
            sheet.column_dimensions[get_column_letter(column)].width = 18

        for student in week['students']:
            values = []
            for day in dates:
                cell = student['cells'][day['date']]
                grade = cell['grade']
                attendance = cell['attendance']
                parts = []
                if grade:
                    parts.append(str(grade['value']))
                if attendance:
                    parts.append(ATTENDANCE_LABELS[attendance['status']])
                values.append(' / '.join(parts) or None)
            sheet.append([
                student['full_name'], *values, student['avg_grade'], student['attendance_rate'] / 100,
            ])
            row = sheet[sheet.max_row]
            row[0].data_type = 's'  # A name starting with "=" is still plain text.
            for cell in row[1:]:
                cell.alignment = Alignment(horizontal='center')
            row[-1].number_format = '0.00%'

        stream = BytesIO()
        workbook.save(stream)
        stream.seek(0)
        filename = f"journal_{week['assignment']['id']}_{week['week_start']}.xlsx"
        return FileResponse(stream, as_attachment=True, filename=filename, content_type=XLSX_TYPE)
