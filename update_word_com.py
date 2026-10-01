import win32com.client as win32
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DOCX_PATH = os.path.abspath('report/報告書_前模擬_new.docx')
PDF_PATH = os.path.abspath('report/報告書_前模擬_new.pdf')

word = win32.Dispatch('Word.Application')
word.Visible = False

try:
    doc = word.Documents.Open(DOCX_PATH)
    
    print('Updating all fields and TOCs...')
    # Update all fields in main story
    for f in doc.Fields:
        try:
            f.Update()
        except:
            pass
            
    # Update Tables of Contents
    for i in range(1, doc.TablesOfContents.Count + 1):
        print(f'Updating TOC {i}...')
        doc.TablesOfContents(i).Update()
        
    for i in range(1, doc.TablesOfFigures.Count + 1):
        print(f'Updating TOF {i}...')
        doc.TablesOfFigures(i).Update()

    # Let's inspect the updated TOC 2 (List of figures)
    print('\n=== Updated TOC 2 (List of Figures) ===')
    print(doc.TablesOfContents(2).Range.Text.strip())
    
    # Save the updated docx
    doc.Save()
    print('\nSaved docx successfully.')
    
    # Export to PDF (17 = wdExportFormatPDF)
    doc.ExportAsFixedFormat(PDF_PATH, 17)
    print(f'Exported to PDF: {PDF_PATH}')
    
finally:
    doc.Close(False)
    word.Quit()

print('Done!')
