/**
 * PANOPTILENS API Client
 * Centralized API communication layer for frontend-backend integration
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * API Error class for structured error handling
 */
export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

/**
 * Generic API request handler with error handling and timeout
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  timeout: number = 30000
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      signal: controller.signal,
      headers: {
        ...options.headers,
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = { message: response.statusText };
      }

      throw new APIError(
        errorData.message || errorData.detail?.message || errorData.detail || `HTTP ${response.status}`,
        response.status,
        errorData.code || errorData.error || errorData.detail?.error,
        errorData
      );
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof APIError) {
      throw error;
    }

    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        throw new APIError('Request timeout', 408);
      }
      throw new APIError(error.message, 0);
    }

    throw new APIError('Unknown error occurred', 0);
  }
}

/**
 * Type definitions for API responses
 */

export interface ImageHash {
  md5: string;
  sha1: string;
  sha256: string;
  sha512: string;
}

export interface CameraMetadata {
  make: string | null;
  model: string | null;
  lens: string | null;
  software: string | null;
}

export interface CaptureMetadata {
  dateTimeOriginal: string | null;
  createDate: string | null;
  modifyDate: string | null;
  dateTimeDigitized?: string | null;
  offsetTimeOriginal?: string | null;
  offsetTimeDigitized?: string | null;
  offsetTime?: string | null;
  timezoneUnknown?: boolean;
  timezoneUnknowns?: Record<string, boolean>;
  serverReceivedAt?: string | null;
  fileUploadTimestamp?: string | null;
}

export interface AddressMetadata {
  country: string | null;
  province: string | null;
  city: string | null;
  district: string | null;
  road: string | null;
  formatted: string | null;
}

export interface GeographicMetadata {
  latitude: number;
  longitude: number;
  altitude: number | null;
  gpsTimestamp: string | null;
  direction?: number | null;
  address?: AddressMetadata | null;
}

export interface ImageDetails {
  width: number | null;
  height: number | null;
  orientation: string | number | null;
  colorSpace: string | null;
  resolution: unknown | null;
  format?: string | null;
  mode?: string | null;
}

export interface ImageMetadata {
  camera: CameraMetadata;
  capture: CaptureMetadata;
  geographic: GeographicMetadata | null;
  image: ImageDetails;
  status: "PRESENT" | "NOT_PRESENT" | "FAILED" | string;
  gpsStatus: "PRESENT" | "NOT_PRESENT" | "INVALID" | string;
  raw: Record<string, unknown>;
  derived?: Record<string, unknown>;
}

export interface ForensicStatus {
  mime_validated: boolean | null;
  magic_bytes_validated: boolean | null;
  extension_match: boolean | null;
  image_decoded: boolean | null;
  metadata_extracted: boolean | null;
  metadata_consistency: string;
}

export interface ImageResponse {
  id: string;
  filename: string;
  size: number;
  type: string;
  format: string | null;
  mode: string | null;
  url: string;
  hash: ImageHash;
  metadata: ImageMetadata;
  forensic: ForensicStatus;
  uploadedAt: string;
  processedAt: string | null;
  metadataExtractedAt: string | null;
  caseId?: string | null;
  userId?: string | null;
  isDeleted: boolean;
  deletedAt: string | null;
  tags: string[];
  analystNotes: string | null;
}

export interface BulkUploadResponse {
  results: ImageResponse[];
  errors: Array<{ filename: string | null; error: string; message: string }>;
}

export interface IntegrityVerification {
  imageId: string;
  status: "VERIFIED" | "TAMPERED" | "MISSING" | "UNREADABLE";
  expectedSha256: string;
  actualSha256: string | null;
  checkedAt: string;
}

export interface DeletionAuditEntry {
  id: string;
  imageId: string;
  filename: string;
  sha256: string | null;
  action: "SOFT_DELETE" | "HARD_DELETE";
  occurredAt: string;
}

export interface CaseResponse {
  id: string;
  name: string;
  description: string | null;
  status: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * Image API functions
 */

/**
 * Upload an image file for forensic analysis
 */
export async function uploadImage(
  file: File,
  caseId?: string
): Promise<ImageResponse> {
  const formData = new FormData();
  formData.append('file', file);
  
  if (caseId) {
    formData.append('case_id', caseId);
  }

  return apiRequest<ImageResponse>('/api/images/upload', {
    method: 'POST',
    body: formData,
  }, 60000); // 60s timeout for upload
}

export async function uploadImages(
  files: File[],
  caseId?: string
): Promise<BulkUploadResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  if (caseId) formData.append("case_id", caseId);

  return apiRequest<BulkUploadResponse>("/api/images/upload/bulk", {
    method: "POST",
    body: formData,
  }, 300000);
}

/**
 * Get image details by ID
 */
export async function getImage(imageId: string): Promise<ImageResponse> {
  return apiRequest<ImageResponse>(`/api/images/${imageId}`);
}

/**
 * Get all images (optionally filtered by case)
 */
export async function getImages(caseId?: string): Promise<ImageResponse[]> {
  const query = caseId ? `?case_id=${caseId}` : '';
  return apiRequest<ImageResponse[]>(`/api/images${query}`);
}

/**
 * Delete an image by ID
 */
export async function deleteImage(imageId: string): Promise<void> {
  return apiRequest<void>(`/api/images/${imageId}`, {
    method: 'DELETE',
  });
}

export async function getTrashImages(): Promise<ImageResponse[]> {
  return apiRequest<ImageResponse[]>("/api/images/trash");
}

export async function restoreImage(imageId: string): Promise<ImageResponse> {
  return apiRequest<ImageResponse>(`/api/images/trash/${imageId}/restore`, { method: "POST" });
}

export async function hardDeleteImage(imageId: string): Promise<void> {
  return apiRequest<void>(`/api/images/trash/${imageId}`, { method: "DELETE" });
}

export async function emptyTrash(): Promise<{ deleted: string[]; failed: Array<{ id: string; message: string }> }> {
  return apiRequest("/api/images/trash/empty/all", { method: "DELETE" });
}

export async function updateImageAnnotations(
  imageId: string,
  annotations: { tags?: string[]; analystNotes?: string | null }
): Promise<{ tags: string[]; analystNotes: string | null }> {
  return apiRequest(`/api/images/${imageId}/annotations`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(annotations),
  });
}

export async function verifyImageIntegrity(imageId: string): Promise<IntegrityVerification> {
  return apiRequest<IntegrityVerification>(`/api/images/${imageId}/verify-integrity`, { method: "POST" });
}

export function imageReportUrl(imageId: string): string {
  return `${API_BASE_URL}/api/images/${imageId}/export`;
}

export function caseReportUrl(caseId: string): string {
  return `${API_BASE_URL}/api/cases/${caseId}/export`;
}

/**
 * Get image metadata by ID
 */
export async function getImageMetadata(imageId: string): Promise<ImageMetadata> {
  return apiRequest<ImageMetadata>(`/api/metadata/${imageId}`);
}

/**
 * Get forensic analysis for an image
 */
export async function getImageForensics(imageId: string): Promise<any> {
  return apiRequest<any>(`/api/forensics/${imageId}`);
}

/**
 * Case API functions
 */

/**
 * Create a new case
 */
export async function createCase(
  name: string,
  description?: string
): Promise<CaseResponse> {
  return apiRequest<CaseResponse>('/api/cases/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ name, description }),
  });
}

/**
 * Get all cases
 */
export async function getCases(): Promise<CaseResponse[]> {
  return apiRequest<CaseResponse[]>('/api/cases/');
}

/**
 * Get case details by ID
 */
export async function getCase(caseId: string): Promise<CaseResponse> {
  return apiRequest<CaseResponse>(`/api/cases/${caseId}`);
}

/**
 * Health check
 */
export async function healthCheck(): Promise<{ status: string }> {
  return apiRequest<{ status: string }>('/health');
}

/**
 * Check if API is available
 */
export async function isAPIAvailable(): Promise<boolean> {
  try {
    await healthCheck();
    return true;
  } catch {
    return false;
  }
}
