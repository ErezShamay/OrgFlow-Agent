declare module "pdfmake/interfaces" {
  export type Alignment = "left" | "right" | "center" | "justify";

  export interface ContentImage {
    image: string;
    width?: number;
    alignment?: Alignment;
    margin?: number | [number, number, number, number];
  }

  export interface ContentText {
    text: string;
    style?: string;
    alignment?: Alignment;
    margin?: number | [number, number, number, number];
    fontSize?: number;
    color?: string;
    bold?: boolean;
  }

  export interface ContentColumn {
    width?: number | string;
    stack?: Content[];
    text?: string;
    alignment?: Alignment;
  }

  export interface ContentColumns {
    columns: ContentColumn[];
    margin?: number | [number, number, number, number];
  }

  export interface ContentStack {
    stack: Content[];
    alignment?: Alignment;
    margin?: number | [number, number, number, number];
  }

  export interface ContentTable {
    table: {
      headerRows?: number;
      widths?: Array<string | number>;
      body: string[][];
    };
    layout?: string;
    margin?: number | [number, number, number, number];
  }

  export interface ContentList {
    ul?: string[];
    ol?: string[];
    alignment?: Alignment;
    margin?: number | [number, number, number, number];
  }

  export type Content =
    | string
    | ContentText
    | ContentImage
    | ContentColumns
    | ContentStack
    | ContentTable
    | ContentList;

  export interface StyleDictionary {
    [key: string]: {
      fontSize?: number;
      bold?: boolean;
      color?: string;
    };
  }

  export interface TDocumentDefinitions {
    info?: {
      title?: string;
    };
    pageMargins?: [number, number, number, number];
    defaultStyle?: {
      font?: string;
      fontSize?: number;
      alignment?: Alignment;
    };
    styles?: StyleDictionary;
    footer?:
      | Content
      | ((
          currentPage: number,
          pageCount: number
        ) => Content | ContentColumns);
    content?: Content | Content[];
  }
}

declare module "pdfmake/build/pdfmake" {
  import type { TDocumentDefinitions } from "pdfmake/interfaces";

  interface PdfDocument {
    getBlob(callback: (blob: Blob) => void): void;
    download(filename?: string): void;
  }

  interface PdfMakeStatic {
    vfs?: Record<string, string>;
    fonts: Record<
      string,
      {
        normal: string;
        bold: string;
        italics: string;
        bolditalics: string;
      }
    >;
    addVirtualFileSystem?(vfs: Record<string, string>): void;
    addFonts?(
      fonts: Record<
        string,
        {
          normal: string;
          bold: string;
          italics: string;
          bolditalics: string;
        }
      >
    ): void;
    createPdf(docDefinition: TDocumentDefinitions): PdfDocument;
  }

  const pdfMake: PdfMakeStatic;
  export default pdfMake;
}

declare module "pdfmake/build/vfs_fonts" {
  const pdfFonts: {
    pdfMake: {
      vfs: Record<string, string>;
    };
  };
  export default pdfFonts;
}
