'use strict';

 

const PRINT_DIALOG_DELAY = 500;

class DocumentPrint {
    static setup () {
        const printFrame = document.getElementById('document-print-frame');

        if (printFrame === null) {
            return;
        }

        const documentPrint = new DocumentPrint(printFrame);
        documentPrint.initialize();

        return documentPrint;
    }

    constructor (printFrame) {
        this.printDialogRequested = false;
        this.printFrame = printFrame;
    }

    initialize () {
        this.printFrame.addEventListener(
            'load', () => {
                window.setTimeout(
                    () => {
                        this.requestPrintDialog();
                    }, PRINT_DIALOG_DELAY
                );
            }
        );
    }

    requestPrintDialog () {
        if (this.printDialogRequested) {
            return;
        }

        this.printDialogRequested = true;

        try {
            this.printFrame.contentWindow.focus();
            this.printFrame.contentWindow.print();
        } catch (error) {
            
            
            
            console.debug('Unable to open the print dialog: ', error);
        }
    }
}

DocumentPrint.setup();
