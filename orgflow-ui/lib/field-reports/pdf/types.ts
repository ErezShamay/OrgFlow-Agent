export type OrganizationProfileSnapshot = {
  organization_id?: string;
  organization_name?: string | null;
  contact_email?: string | null;
  report_phone?: string | null;
  report_address_line?: string | null;
  report_city?: string | null;
  report_tagline?: string | null;
  logo_storage_path?: string | null;
  logo_url?: string | null;
};

export type PdfReportLine = {
  id: string;
  sort_order?: number;
  location?: string | null;
  trade?: string | null;
  status?: string | null;
  description?: string | null;
  notes?: string | null;
  severity?: string | null;
  standard_ref?: string | null;
  catalog_reference_id?: string | null;
  issue_id?: string | null;
  group_key?: string | null;
  group_label_he?: string | null;
  has_photo?: boolean;
  photo_url?: string | null;
  photo_ids?: string[];
  photos?: Array<{ id: string; url: string }>;
};

export type PdfVisitReport = {
  id: string;
  client_report_uuid?: string;
  project_id?: string | null;
  server_report_id?: string | null;
  status?: string | null;
  project_name?: string | null;
  visit_type: string;
  visit_type_label_he: string;
  visit_date: string;
  header_fields: Record<string, unknown>;
  lines: PdfReportLine[];
  organization_profile_snapshot?: OrganizationProfileSnapshot | null;
};

export type PdfInspectorProfile = {
  full_name?: string | null;
  professional_title?: string | null;
  license_number?: string | null;
};

export type LinePhotoData = {
  lineId: string;
  photoId?: string;
  dataUrl: string;
};

export type ChecklistPhotoData = {
  checklistItemId: string;
  photoId?: string;
  dataUrl: string;
};

export type VisitReportPdfInput = {
  report: PdfVisitReport;
  inspector?: PdfInspectorProfile | null;
  linePhotos?: LinePhotoData[];
  checklistPhotos?: ChecklistPhotoData[];
  logoDataUrl?: string | null;
  illustrationDataUrl?: string | null;
  generatedAt?: Date;
  lineIssueMarkers?: ReadonlyMap<string, string>;
};
