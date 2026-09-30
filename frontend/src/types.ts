export type LineType = 'Material' | 'Work' | 'Other';
export interface Project { id: string; name: string; customer: string; system_type: string; updated_at: string }
export interface Line {
  id: string; project_id: string; system_type: string; line_type: LineType;
  project_description: string; output_description: string; technical_reference: string;
  source_position: string; source_page: number | null; source_raw_text: string;
  unit: string; quantity: string; sistela_code: string; sistela_original_description: string;
  material_price: string | null; work_price: string | null; confidence: string | null;
  mapping_status: 'unmapped' | 'suggested' | 'confirmed' | 'rejected' | 'needs_review'; notes: string;
  review_data?: {automatic?:boolean; code_type?:string; normative_unit?:string; suggestion?:{origin?:string;catalog_verified?:boolean}; conversion?: {source_quantity:string;source_unit:string;target_quantity:string;target_unit:string;confirmed_by_user:boolean}; manual?:boolean; price_status?:string};
  source_document_id?: string | null;
  version: number; sort_order: number; entered_at: string | null;
}
export interface ImportRun { id: string; status: string; rows_detected: number; pages: number[]; error_message: string | null; warnings: { code: string; message: string; page?: number }[]; options?: import('./PdfDiagnostics').PdfOptions }
export interface Capability { id: string; name: string; status: string; production: boolean; limitation: string }
export interface Suggestion { mapping_id: string; sistela_code: string; sistela_description: string; source_unit: string; confidence: string; method: string; confirmed_count: number; compatible: boolean; origin?: 'user' | 'historical' | 'catalog'; historical_confirmed?: boolean; usage_count?: number; project_count?: number; estimate_count?: number; matching_descriptions?: string[]; evidence_quality?: string[]; evidence_ids?: string[]; last_used_at?: string | null; source_date?: string | null; unit_compatibility?: {status:string;source:string;target:string;factor:string|null} }
export const editableKeys = ['system_type','line_type','project_description','technical_reference','unit','quantity','output_description','material_price','work_price','notes','sistela_code','sistela_original_description'] as const;
export const editable = (line: Line) => Object.fromEntries(editableKeys.map(k => [k, line[k]]));
export const blankLine = (system: string) => ({ system_type: system, line_type: 'Other', project_description: 'Nauja eilutė', output_description: 'Nauja eilutė', quantity: '1', unit: 'vnt.', notes: '', technical_reference: '', material_price: null, work_price: null, sistela_code: '', sistela_original_description: '' });
export const typeLabel: Record<LineType, string> = { Material: 'Medžiaga', Work: 'Darbas', Other: 'Kita' };
