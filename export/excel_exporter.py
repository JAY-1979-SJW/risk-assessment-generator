# -*- coding: utf-8 -*-
"""
엑셀 내보내기 모듈
KRAS 표준 양식에 맞게 엑셀 파일 생성
"""

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from datetime import datetime


class ExcelExporter:
    """엑셀 내보내기 클래스"""

    def __init__(self, data_manager):
        self.data_manager = data_manager

        # 스타일 정의
        self.header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        self.header_font = Font(bold=True, color="FFFFFF", size=10, name="맑은 고딕")
        self.title_font = Font(bold=True, size=16, name="맑은 고딕")
        self.normal_font = Font(size=10, name="맑은 고딕")

        self.thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        self.center_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
        self.left_align = Alignment(horizontal='left', vertical='center', wrap_text=True)

        # 위험성 등급별 색상
        self.risk_colors = {
            "낮음": PatternFill(start_color="92D050", end_color="92D050", fill_type="solid"),
            "보통": PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid"),
            "높음": PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid"),
        }

    def export(self, file_path: str):
        """엑셀 파일로 내보내기"""
        wb = Workbook()

        # 기본 시트 제거
        wb.remove(wb.active)

        # 시트 생성 (순서대로)
        self._create_safety_policy_sheet(wb)
        self._create_organization_sheet(wb)
        self._create_risk_criteria_sheet(wb)
        self._create_meeting_sheet(wb)
        self._create_assessment_sheet(wb)

        # 저장
        wb.save(file_path)
        print(f"엑셀 파일 생성 완료: {file_path}")

    def _create_safety_policy_sheet(self, wb):
        """안전보건방침 및 추진목표 시트"""
        ws = wb.create_sheet("안전보건방침 및 추진목표")

        info = self.data_manager.company_info

        # 제목
        ws.merge_cells('A1:H1')
        ws['A1'] = "안전보건방침 및 추진목표"
        ws['A1'].font = self.title_font
        ws['A1'].alignment = self.center_align

        # 회사정보 섹션
        row = 3
        ws.merge_cells(f'A{row}:B{row}')
        ws[f'A{row}'] = "회사명"
        ws[f'A{row}'].fill = self.header_fill
        ws[f'A{row}'].font = self.header_font
        ws[f'A{row}'].border = self.thin_border
        ws[f'A{row}'].alignment = self.center_align

        ws.merge_cells(f'C{row}:E{row}')
        ws[f'C{row}'] = info.get("company_name", "")
        ws[f'C{row}'].border = self.thin_border
        ws[f'C{row}'].font = self.normal_font

        ws[f'F{row}'] = "대표자"
        ws[f'F{row}'].fill = self.header_fill
        ws[f'F{row}'].font = self.header_font
        ws[f'F{row}'].border = self.thin_border
        ws[f'F{row}'].alignment = self.center_align

        ws.merge_cells(f'G{row}:H{row}')
        ws[f'G{row}'] = info.get("ceo_name", "")
        ws[f'G{row}'].border = self.thin_border
        ws[f'G{row}'].font = self.normal_font

        row = 4
        ws.merge_cells(f'A{row}:B{row}')
        ws[f'A{row}'] = "업종"
        ws[f'A{row}'].fill = self.header_fill
        ws[f'A{row}'].font = self.header_font
        ws[f'A{row}'].border = self.thin_border
        ws[f'A{row}'].alignment = self.center_align

        ws.merge_cells(f'C{row}:E{row}')
        ws[f'C{row}'] = info.get("business_type", "")
        ws[f'C{row}'].border = self.thin_border
        ws[f'C{row}'].font = self.normal_font

        ws[f'F{row}'] = "평가유형"
        ws[f'F{row}'].fill = self.header_fill
        ws[f'F{row}'].font = self.header_font
        ws[f'F{row}'].border = self.thin_border
        ws[f'F{row}'].alignment = self.center_align

        ws.merge_cells(f'G{row}:H{row}')
        ws[f'G{row}'] = info.get("eval_type", "")
        ws[f'G{row}'].border = self.thin_border
        ws[f'G{row}'].font = self.normal_font

        row = 5
        ws.merge_cells(f'A{row}:B{row}')
        ws[f'A{row}'] = "현장명"
        ws[f'A{row}'].fill = self.header_fill
        ws[f'A{row}'].font = self.header_font
        ws[f'A{row}'].border = self.thin_border
        ws[f'A{row}'].alignment = self.center_align

        ws.merge_cells(f'C{row}:E{row}')
        ws[f'C{row}'] = info.get("site_name", "")
        ws[f'C{row}'].border = self.thin_border
        ws[f'C{row}'].font = self.normal_font

        ws[f'F{row}'] = "평가일자"
        ws[f'F{row}'].fill = self.header_fill
        ws[f'F{row}'].font = self.header_font
        ws[f'F{row}'].border = self.thin_border
        ws[f'F{row}'].alignment = self.center_align

        ws.merge_cells(f'G{row}:H{row}')
        ws[f'G{row}'] = info.get("eval_date", "")
        ws[f'G{row}'].border = self.thin_border
        ws[f'G{row}'].font = self.normal_font

        row = 6
        ws.merge_cells(f'A{row}:B{row}')
        ws[f'A{row}'] = "주소"
        ws[f'A{row}'].fill = self.header_fill
        ws[f'A{row}'].font = self.header_font
        ws[f'A{row}'].border = self.thin_border
        ws[f'A{row}'].alignment = self.center_align

        ws.merge_cells(f'C{row}:H{row}')
        ws[f'C{row}'] = info.get("address", "")
        ws[f'C{row}'].border = self.thin_border
        ws[f'C{row}'].font = self.normal_font

        # 안전보건방침 섹션
        row = 8
        ws.merge_cells(f'A{row}:H{row}')
        ws[f'A{row}'] = "안전보건방침"
        ws[f'A{row}'].fill = self.header_fill
        ws[f'A{row}'].font = self.header_font
        ws[f'A{row}'].border = self.thin_border
        ws[f'A{row}'].alignment = self.center_align

        row = 9
        ws.merge_cells(f'A{row}:H{row + 7}')
        ws[f'A{row}'] = info.get("safety_policy", "")
        ws[f'A{row}'].font = self.normal_font
        ws[f'A{row}'].alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
        ws[f'A{row}'].border = self.thin_border

        # 테두리 적용
        for r in range(row, row + 8):
            for c in range(1, 9):
                ws.cell(row=r, column=c).border = self.thin_border

        # 추진목표 섹션
        row = 18
        ws.merge_cells(f'A{row}:H{row}')
        ws[f'A{row}'] = "추진목표"
        ws[f'A{row}'].fill = self.header_fill
        ws[f'A{row}'].font = self.header_font
        ws[f'A{row}'].border = self.thin_border
        ws[f'A{row}'].alignment = self.center_align

        row = 19
        ws.merge_cells(f'A{row}:H{row + 5}')
        ws[f'A{row}'] = info.get("safety_goal", "")
        ws[f'A{row}'].font = self.normal_font
        ws[f'A{row}'].alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
        ws[f'A{row}'].border = self.thin_border

        # 테두리 적용
        for r in range(row, row + 6):
            for c in range(1, 9):
                ws.cell(row=r, column=c).border = self.thin_border

        # 열 너비 조정
        for col in range(1, 9):
            ws.column_dimensions[get_column_letter(col)].width = 15

        # 행 높이 조정
        ws.row_dimensions[1].height = 30
        for r in range(9, 17):
            ws.row_dimensions[r].height = 20
        for r in range(19, 25):
            ws.row_dimensions[r].height = 18

    def _create_organization_sheet(self, wb):
        """위험성평가 조직구성 시트"""
        ws = wb.create_sheet("위험성평가 조직구성")

        info = self.data_manager.company_info
        org = self.data_manager.organization

        # 제목
        ws.merge_cells('A1:F1')
        ws['A1'] = "위험성평가 실시 담당 조직 구성"
        ws['A1'].font = self.title_font
        ws['A1'].alignment = self.center_align

        # 부제목
        ws.merge_cells('A2:F2')
        ws['A2'] = "(표준실시규정 제3조, 제4조 참조)"
        ws['A2'].font = Font(size=10, color="666666", name="맑은 고딕")
        ws['A2'].alignment = self.center_align

        # 회사정보
        row = 4
        ws.merge_cells(f'A{row}:B{row}')
        ws[f'A{row}'] = "회사명"
        ws[f'A{row}'].fill = self.header_fill
        ws[f'A{row}'].font = self.header_font
        ws[f'A{row}'].border = self.thin_border
        ws[f'A{row}'].alignment = self.center_align

        ws.merge_cells(f'C{row}:F{row}')
        ws[f'C{row}'] = info.get("company_name", "")
        ws[f'C{row}'].border = self.thin_border
        ws[f'C{row}'].font = self.normal_font

        row = 5
        ws.merge_cells(f'A{row}:B{row}')
        ws[f'A{row}'] = "현장명"
        ws[f'A{row}'].fill = self.header_fill
        ws[f'A{row}'].font = self.header_font
        ws[f'A{row}'].border = self.thin_border
        ws[f'A{row}'].alignment = self.center_align

        ws.merge_cells(f'C{row}:F{row}')
        ws[f'C{row}'] = info.get("site_name", "")
        ws[f'C{row}'].border = self.thin_border
        ws[f'C{row}'].font = self.normal_font

        # 조직 테이블 헤더
        row = 7
        headers = ["직위/직책", "성명", "역할", "책임"]
        col_widths = [20, 15, 15, 50]

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.fill = self.header_fill
            cell.font = self.header_font
            cell.border = self.thin_border
            cell.alignment = self.center_align

        # 조직 데이터
        members = org.get("members", [])
        for member in members:
            row += 1
            ws.cell(row=row, column=1, value=member.get("position", "")).border = self.thin_border
            ws.cell(row=row, column=2, value=member.get("name", "")).border = self.thin_border
            ws.cell(row=row, column=3, value=member.get("role", "")).border = self.thin_border
            ws.cell(row=row, column=4, value=member.get("responsibility", "")).border = self.thin_border

            ws.cell(row=row, column=1).alignment = self.center_align
            ws.cell(row=row, column=2).alignment = self.center_align
            ws.cell(row=row, column=3).alignment = self.center_align
            ws.cell(row=row, column=4).alignment = self.left_align
            ws.cell(row=row, column=4).font = self.normal_font

        # 열 너비 조정
        for col, width in enumerate(col_widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = width

        # 행 높이
        ws.row_dimensions[1].height = 30
        for r in range(7, row + 1):
            ws.row_dimensions[r].height = 25

    def _create_risk_criteria_sheet(self, wb):
        """위험성 추정 및 결정 시트"""
        ws = wb.create_sheet("위험성 추정 및 결정")

        # 제목
        ws.merge_cells('A1:G1')
        ws['A1'] = "위험성 추정 및 결정 방법"
        ws['A1'].font = self.title_font
        ws['A1'].alignment = self.center_align

        # 부제목
        ws.merge_cells('A3:G3')
        ws['A3'] = "곱셈식에 의한 위험성 추정 및 결정표"
        ws['A3'].font = Font(bold=True, size=12, name="맑은 고딕")
        ws['A3'].alignment = self.center_align

        # 실시방법
        ws.merge_cells('A4:G4')
        ws['A4'] = "실시방법: 가능성과 중대성을 추정한 수치를 곱셈에 의해 위험성을 구하고 위험성 수준을 결정함"
        ws['A4'].font = self.normal_font
        ws['A4'].alignment = self.left_align

        # 가능성(빈도) 테이블
        row = 6
        ws.merge_cells(f'A{row}:G{row}')
        ws[f'A{row}'] = "가능성: 사고나 질병으로 이어질 가능성(확률)을 파악하는 것으로 발생빈도 수준을 측정"
        ws[f'A{row}'].font = self.normal_font

        row = 7
        headers = ["구분", "가능성", "기준"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.fill = self.header_fill
            cell.font = self.header_font
            cell.border = self.thin_border
            cell.alignment = self.center_align

        possibility_data = [
            ("상", 3, "발생가능성이 높음. 일상적으로 장시간 이루어지는 작업에 수반하는 것으로 피하기 어려운 것"),
            ("중", 2, "발생가능성이 있음. 일상적인 작업에 수반하는 것으로 피할 수 있는 것"),
            ("하", 1, "발생가능성이 낮음. 비정상적인 작업에 수반하는 것으로 피할 수 있는 것"),
        ]

        for data in possibility_data:
            row += 1
            ws.cell(row=row, column=1, value=data[0]).border = self.thin_border
            ws.cell(row=row, column=2, value=data[1]).border = self.thin_border
            ws.merge_cells(f'C{row}:G{row}')
            ws.cell(row=row, column=3, value=data[2]).border = self.thin_border
            ws.cell(row=row, column=1).alignment = self.center_align
            ws.cell(row=row, column=2).alignment = self.center_align
            ws.cell(row=row, column=3).alignment = self.left_align

        # 중대성(강도) 테이블
        row += 2
        ws.merge_cells(f'A{row}:G{row}')
        ws[f'A{row}'] = "중대성: 사고나 질병으로 이어졌을 때 그 중대성(강도)을 파악하는 것으로 부상의 경중(심각성)을 측정"
        ws[f'A{row}'].font = self.normal_font

        row += 1
        headers = ["구분", "중대성", "기준"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.fill = self.header_fill
            cell.font = self.header_font
            cell.border = self.thin_border
            cell.alignment = self.center_align

        severity_data = [
            ("대", 3, "사망을 초래할 수 있는 사고. 신체 일부에 영구손상을 수반하는 것"),
            ("중", 2, "휴업재해, 한번에 다수의 피해자가 수반하는 것. 실명, 절단 등 상해를 초래할 수 있는 사고"),
            ("소", 1, "아차 사고. 처치 후 바로 원래의 작업을 수행할 수 있는 경미한 부상 또는 질병"),
        ]

        for data in severity_data:
            row += 1
            ws.cell(row=row, column=1, value=data[0]).border = self.thin_border
            ws.cell(row=row, column=2, value=data[1]).border = self.thin_border
            ws.merge_cells(f'C{row}:G{row}')
            ws.cell(row=row, column=3, value=data[2]).border = self.thin_border
            ws.cell(row=row, column=1).alignment = self.center_align
            ws.cell(row=row, column=2).alignment = self.center_align
            ws.cell(row=row, column=3).alignment = self.left_align

        # 공식
        row += 2
        ws.merge_cells(f'A{row}:G{row}')
        ws[f'A{row}'] = "※ 가능성(빈도) × 중대성(강도) = 위험성 추정"
        ws[f'A{row}'].font = Font(bold=True, size=11, color="FF0000", name="맑은 고딕")

        # 위험성 결정
        row += 2
        ws.merge_cells(f'A{row}:G{row}')
        ws[f'A{row}'] = "위험성결정: 평가 3단계로 구분하고 평가 점수가 높은 순서대로 우선순위 결정"
        ws[f'A{row}'].font = self.normal_font

        row += 1
        headers = ["위험성 수준", "등급", "허용가능범위", "비고"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.fill = self.header_fill
            cell.font = self.header_font
            cell.border = self.thin_border
            cell.alignment = self.center_align

        decision_data = [
            ("1~2", "낮음", "허용가능", "근로자에게 유해 위험성 정보를 제공 및 교육"),
            ("3~4", "보통", "허용 불가능", "안전보건대책을 수립하고 개선"),
            ("6~9", "높음", "허용 불가능", "작업을 지속하려면 즉시 개선을 실행"),
        ]

        colors = [
            PatternFill(start_color="92D050", end_color="92D050", fill_type="solid"),
            PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid"),
            PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid"),
        ]

        for i, data in enumerate(decision_data):
            row += 1
            ws.cell(row=row, column=1, value=data[0]).border = self.thin_border
            cell = ws.cell(row=row, column=2, value=data[1])
            cell.border = self.thin_border
            cell.fill = colors[i]
            ws.cell(row=row, column=3, value=data[2]).border = self.thin_border
            ws.merge_cells(f'D{row}:G{row}')
            ws.cell(row=row, column=4, value=data[3]).border = self.thin_border

            for col in range(1, 5):
                ws.cell(row=row, column=col).alignment = self.center_align

        # 열 너비 조정
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 15
        ws.column_dimensions['F'].width = 15
        ws.column_dimensions['G'].width = 30

    def _create_meeting_sheet(self, wb):
        """위험성평가 회의 결과 시트"""
        ws = wb.create_sheet("위험성평가 회의 결과")

        meeting = self.data_manager.meeting

        # 제목
        ws.merge_cells('A1:H1')
        ws['A1'] = "위험성 평가 회의 결과"
        ws['A1'].font = self.title_font
        ws['A1'].alignment = self.center_align

        # 회의일시
        ws.merge_cells('A3:B3')
        ws['A3'] = "회의일시"
        ws['A3'].font = self.normal_font
        ws['A3'].border = self.thin_border
        ws['A3'].alignment = self.center_align

        ws.merge_cells('C3:H3')
        date_str = meeting.get("date", "")
        time_start = meeting.get("time_start", "")
        time_end = meeting.get("time_end", "")
        ws['C3'] = f"{date_str}  {time_start} ~ {time_end}"
        ws['C3'].border = self.thin_border

        # 회의장소
        ws.merge_cells('A4:B4')
        ws['A4'] = "회의장소"
        ws['A4'].font = self.normal_font
        ws['A4'].border = self.thin_border
        ws['A4'].alignment = self.center_align

        ws.merge_cells('C4:H4')
        ws['C4'] = meeting.get("location", "")
        ws['C4'].border = self.thin_border

        # 회의내용
        ws.merge_cells('A6:H6')
        ws['A6'] = "□ 회의내용"
        ws['A6'].font = Font(bold=True, size=11, name="맑은 고딕")

        ws.merge_cells('A7:H15')
        ws['A7'] = meeting.get("content", "")
        ws['A7'].alignment = self.left_align
        ws['A7'].font = self.normal_font

        # 참석자 명단
        ws.merge_cells('A17:H17')
        ws['A17'] = "□ 참석자 명단"
        ws['A17'].font = Font(bold=True, size=11, name="맑은 고딕")

        row = 18
        headers = ["소속/직책", "성명", "서명", "", "소속/직책", "성명", "서명", ""]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            if header:
                cell.fill = self.header_fill
                cell.font = self.header_font
            cell.border = self.thin_border
            cell.alignment = self.center_align

        attendees = meeting.get("attendees", [])
        for i, attendee in enumerate(attendees):
            row = 19 + (i // 2)
            if i % 2 == 0:
                ws.cell(row=row, column=1, value=attendee.get("department", "")).border = self.thin_border
                ws.cell(row=row, column=2, value=attendee.get("name", "")).border = self.thin_border
                ws.cell(row=row, column=3, value="").border = self.thin_border
            else:
                ws.cell(row=row, column=5, value=attendee.get("department", "")).border = self.thin_border
                ws.cell(row=row, column=6, value=attendee.get("name", "")).border = self.thin_border
                ws.cell(row=row, column=7, value="").border = self.thin_border

        # 열 너비
        for col in range(1, 9):
            ws.column_dimensions[get_column_letter(col)].width = 15

    def _create_assessment_sheet(self, wb):
        """위험성평가 실시표 시트"""
        ws = wb.create_sheet("위험성평가실시")

        info = self.data_manager.company_info

        # KRAS 헤더
        ws.merge_cells('A1:P1')
        ws['A1'] = "KRAS(표준 위험성평가)"
        ws['A1'].font = Font(bold=True, size=12, name="맑은 고딕")

        ws.merge_cells('A2:P2')
        ws['A2'] = "(http://kras.kosha.or.kr)"
        ws['A2'].font = Font(size=9, name="맑은 고딕")

        # 공정명, 평가일시
        ws.merge_cells('A7:C7')
        ws['A7'] = f"공정명: {info.get('site_name', '')}"
        ws['A7'].font = Font(bold=True, size=11, name="맑은 고딕")

        ws.merge_cells('D7:G7')
        ws['D7'] = "위험성평가"
        ws['D7'].font = Font(bold=True, size=11, name="맑은 고딕")
        ws['D7'].alignment = self.center_align

        ws.merge_cells('N7:P7')
        ws['N7'] = f"평가일시: {info.get('eval_date', '')}"
        ws['N7'].font = Font(size=10, name="맑은 고딕")

        # 헤더 행
        row = 8
        headers = [
            "공정명", "세부작업명", "위험분류", "위험세부분류",
            "위험발생\n상황 및 결과", "관련근거\n(법적기준)", "현재의\n안전보건조치",
            "평가\n척도", "가능성\n(빈도)", "중대성\n(강도)", "위험성",
            "위험성 감소대책", "개선후\n위험성", "개선\n예정일", "완료일", "담당자"
        ]

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.fill = self.header_fill
            cell.font = self.header_font
            cell.border = self.thin_border
            cell.alignment = self.center_align

        # 하위 헤더 (유해위험요인 파악)
        ws.merge_cells('C8:E8')

        # 데이터 행
        for assessment in self.data_manager.assessments:
            row += 1

            current_level = assessment.get("current_risk_level", "")
            after_level = assessment.get("after_risk_level", "")
            current_risk_color = self.risk_colors.get(current_level, PatternFill())
            after_risk_color = self.risk_colors.get(after_level, PatternFill())

            data = [
                assessment.get("process", ""),
                assessment.get("sub_work", ""),
                assessment.get("risk_category", ""),
                assessment.get("risk_detail", ""),
                assessment.get("risk_situation", ""),
                assessment.get("legal_basis", ""),
                assessment.get("current_measures", ""),
                assessment.get("eval_scale", "3x3"),
                self.data_manager.format_possibility(assessment.get("possibility", 1)),
                self.data_manager.format_severity(assessment.get("severity", 1)),
                self.data_manager.format_risk_level(
                    assessment.get("current_risk", 1),
                    assessment.get("current_risk_level", "")
                ),
                assessment.get("reduction_measures", ""),
                self.data_manager.format_risk_level(
                    assessment.get("after_risk", 1),
                    assessment.get("after_risk_level", "")
                ),
                assessment.get("due_date", ""),
                assessment.get("complete_date", ""),
                assessment.get("manager", ""),
            ]

            for col, value in enumerate(data, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.border = self.thin_border
                cell.font = self.normal_font

                # 위험성 컬럼에 색상 적용 (현재/개선후 별도)
                if col == 11:  # 현재 위험성
                    cell.fill = current_risk_color
                    cell.alignment = self.center_align
                elif col == 13:  # 개선후 위험성
                    cell.fill = after_risk_color
                    cell.alignment = self.center_align
                elif col in [8, 9, 10, 14, 15, 16]:
                    cell.alignment = self.center_align
                else:
                    cell.alignment = self.left_align

        # 열 너비 조정
        column_widths = {
            'A': 12, 'B': 18, 'C': 12, 'D': 14, 'E': 35, 'F': 22,
            'G': 20, 'H': 8, 'I': 10, 'J': 10, 'K': 10, 'L': 35,
            'M': 10, 'N': 10, 'O': 10, 'P': 8
        }
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width

        # 행 높이
        for r in range(8, row + 1):
            ws.row_dimensions[r].height = 35
