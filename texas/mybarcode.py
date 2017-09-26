#    mybarcode.py
from reportlab.lib.units import mm
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.barcharts import HorizontalBarChart

class MyBarcodeDrawing(Drawing):
    def __init__(self, text_value, width=300, height=100, *args, **kw):
        width = int(width)
        height = int(height)
        barcode = createBarcodeDrawing('Code128', value=text_value,  barHeight=10*mm, humanReadable=True, height=height, width=width)
        Drawing.__init__(self,barcode.width,barcode.height,*args,**kw)       
        self.add(barcode, name='barcode')
        

if __name__=='__main__':
    #use the standard 'save' method to save barcode.gif, barcode.pdf etc
    #for quick feedback while working.
    MyBarcodeDrawing("HELLO WORLD").save(formats=['gif','pdf'],outDir='.',fnRoot='barcode')
