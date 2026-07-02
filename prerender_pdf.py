import os
import fitz

def extract_pdf_pages():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(base_dir, "static", "pdf", "NPP_Failures_size_redue.pdf")
    output_dir = os.path.join(base_dir, "static", "pdf_pages")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"Total pages to extract: {total_pages}")
    
    for i in range(total_pages):
        out_path = os.path.join(output_dir, f"page_{i+1}.jpg")
        if os.path.exists(out_path):
            continue
            
        page = doc[i]
        pix = page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2))
        pix.save(out_path, "jpeg", 75)
        if (i+1) % 10 == 0:
            print(f"Extracted {i+1}/{total_pages} pages...")
            
    doc.close()
    print("Done extracting all PDF pages!")

if __name__ == "__main__":
    extract_pdf_pages()
