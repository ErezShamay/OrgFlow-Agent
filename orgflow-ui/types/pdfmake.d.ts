declare module "pdfmake/interfaces" {
  export type Alignment = "left" | "right" | "center" | "justify";

  export interface ContentImage {
    image: string;
    width?: number;
    alignment?: Alignment;
    margin?: number | [number, number, number, number];
    pageBreak?: "before" | "after";
  }

  export interface ContentText {
    text: string;
    style?: string;
    alignment?: Alignment;
    direction?: "ltr" | "rtl";
    margin?: number | [number, number, number, number];
    fontSize?: number;
    font?: string;
    color?: string;
    bold?: boolean;
    fillColor?: string;
    pageBreak?: "before" | "after";
  }

  export interface ContentColumn {
    width?: number | string;
    stack?: Content[];
    text?: string;
    alignment?: Alignment;
    font?: string;
    direction?: "ltr" | "rtl";
    fontSize?: number;
    margin?: number | [number, number, number, number];
  }

  export interface ContentColumns {
    columns: ContentColumn[];
    margin?: number | [number, number, number, number];
    pageBreak?: "before" | "after";
  }

  export interface ContentStack {
    stack: Content[];
    alignment?: Alignment;
    margin?: number | [number, number, number, number];
    pageBreak?: "before" | "after";
  }

  export interface ContentTable {
    table: {
      headerRows?: number;
      widths?: Array<string | number>;
      body: (string | Content)[][];
    };
    layout?: string;
    margin?: number | [number, number, number, number];
    pageBreak?: "before" | "after";
  }

  export interface ContentList {
    ul?: (string | Content)[];
    ol?: (string | Content)[];
    alignment?: Alignment;
    margin?: number | [number, number, number, number];
    pageBreak?: "before" | "after";
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
      font?: string;
      fontSize?: number;
      bold?: boolean;
      color?: string;
      alignment?: Alignment;
      direction?: "ltr" | "rtl";
      fillColor?: string;
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
      direction?: "ltr" | "rtl";
      lineHeight?: number;
    };
    styles?: StyleDictionary;
    header?:
      | Content
      | ((
          currentPage: number,
          pageCount: number
        ) => Content | ContentColumns);
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
    getBlob(): Promise<Blob>;
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
