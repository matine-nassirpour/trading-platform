// -------------------------------------------------------------------
// AUTO-GENERATED FILE — DO NOT EDIT MANUALLY
// Source of truth: trading-platform/contracts/
// Regenerate via: make ts-contracts
// -------------------------------------------------------------------

/* eslint-disable @typescript-eslint/no-unused-vars */

export type SystemStatus = 'UP' | 'DEGRADED' | 'DOWN';

export type HealthStatus = 'OK' | 'DEGRADED' | 'FAILING';

export interface ApiVersionDescriptor {
  readonly year: number;
  readonly revision: number;
}

export interface AdminEndpoints {
  readonly health: string;
  readonly runtimeMetadata: string;
  readonly configDiagnostics: string;
  readonly observabilityDiagnostics: string;
}

export interface AdminHttpDescriptor {
  readonly baseUrl: string;
  readonly endpoints: AdminEndpoints;
}

export interface RuntimeMetadataResponse {
  readonly status: SystemStatus;
  readonly apiVersion: ApiVersionDescriptor;
  readonly adminHttp: AdminHttpDescriptor;
}

export interface HealthResponse {
  readonly status: HealthStatus;
}

export interface ConfigReadyStateSnapshot {
  readonly fsmStatus: string;
  readonly env: Readonly<Record<string, string>> | null;
  readonly settings: Readonly<Record<string, unknown>> | null;
  readonly metadata: Readonly<Record<string, unknown>>;
}

export interface ConfigDiagnosticsResponse {
  readonly schemaVersion: string;
  readonly isConsumable: boolean;
  readonly fingerprint: string | null;
  readonly readyState: ConfigReadyStateSnapshot | null;
  readonly loaderSnapshot: Readonly<Record<string, unknown>> | null;
  readonly reservedEnvKeys: Readonly<Record<string, string | null>>;
  readonly cacheMatchesParams: boolean | null;
  readonly hasValidCache: boolean | null;
  readonly error: string | null;
}

export interface ObservabilityDiagnosticsResponse {
  readonly pipelineUp: boolean;
  readonly loggingOk: boolean;
  readonly loggingSinkUp: boolean;
  readonly tracingOk: boolean;
  readonly tracingUp: boolean;
  readonly metricsHttpOk: boolean;
  readonly runId: string | null;
  readonly correlationId: string | null;
  readonly diagnostics: Readonly<Record<string, unknown>>;
}
