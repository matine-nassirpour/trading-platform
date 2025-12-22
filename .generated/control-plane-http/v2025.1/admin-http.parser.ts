// -------------------------------------------------------------------
// AUTO-GENERATED FILE — DO NOT EDIT MANUALLY
// Source of truth: trading-platform/contracts/
// Regenerate via: make parsed-ts-contracts
// -------------------------------------------------------------------

/* eslint-disable @typescript-eslint/no-unused-vars */

import {
  ApiVersionDescriptor,
  AdminEndpoints,
  AdminHttpDescriptor,
  RuntimeMetadataResponse,
  HealthResponse,
  ConfigReadyStateSnapshot,
  ConfigDiagnosticsResponse,
  ObservabilityDiagnosticsResponse
} from './admin-http.contract';

import { JsonValue } from '../../shared/json-value.contract';

import { HealthStatus, SystemStatus } from './admin-http.contract';


export class ContractParseError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ContractParseError';
  }
}

function expectObject(value: unknown, ctx: string): Record<string, unknown> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    throw new ContractParseError(`${ctx}: expected object`);
  }
  return value as Record<string, unknown>;
}

function expectString(value: unknown, ctx: string): string {
  if (typeof value !== 'string') {
    throw new ContractParseError(`${ctx}: expected string`);
  }
  return value;
}

function expectBoolean(value: unknown, ctx: string): boolean {
  if (typeof value !== 'boolean') {
    throw new ContractParseError(`${ctx}: expected boolean`);
  }
  return value;
}

function expectRecordOfOptionalString(value: unknown, ctx: string): Readonly<Record<string, string | null>> {
  const o = expectObject(value, ctx);
  const result: Record<string, string | null> = {};

  for (const [k, v] of Object.entries(o)) {
    if (v === null) {
      result[k] = null;
    } else if (typeof v === 'string') {
      result[k] = v;
    } else {
      throw new ContractParseError(`${ctx}: invalid value for key ${k}`);
    }
  }

  return result;
}

function expectRecordOfString(
  value: unknown,
  ctx: string,
): Readonly<Record<string, string>> {
  const o = expectObject(value, ctx);
  const result: Record<string, string> = {};

  for (const [k, v] of Object.entries(o)) {
    if (typeof v !== 'string') {
      throw new ContractParseError(`${ctx}: invalid value for key ${k}`);
    }
    result[k] = v;
  }

  return result;
}

function expectOptionalRecordOfString(
  value: unknown,
  ctx: string,
): Readonly<Record<string, string>> | null {
  if (value === null || value === undefined) {
    return null;
  }
  return expectRecordOfString(value, ctx);
}

function expectNumber(value: unknown, ctx: string): number {
  if (typeof value !== 'number') {
    throw new ContractParseError(`${ctx}: expected number`);
  }
  return value;
}

function expectOptionalNumber(value: unknown, ctx: string): number | null {
  if (value === null || value === undefined) {
    return null;
  }
  return expectNumber(value, ctx);
}

function expectArray<T>(
  value: unknown,
  ctx: string,
  parseItem: (v: unknown, ctx: string) => T,
): ReadonlyArray<T> {
  if (!Array.isArray(value)) {
    throw new ContractParseError(`${ctx}: expected array`);
  }

  return value.map((v, i) => {
    try {
      return parseItem(v, `${ctx}[${i}]`);
    } catch (e) {
      if (e instanceof ContractParseError) {
        throw e;
      }
      throw new ContractParseError(`${ctx}[${i}]: ${String(e)}`);
    }
  });
}


function expectArrayOfString(
  value: unknown,
  ctx: string,
): ReadonlyArray<string> {
  return expectArray(value, ctx, (v, itemCtx) => expectString(v, itemCtx));
}

function expectArrayOfNumber(
  value: unknown,
  ctx: string,
): ReadonlyArray<number> {
  return expectArray(value, ctx, (v, itemCtx) => expectNumber(v, itemCtx));
}

function expectArrayOfBoolean(
  value: unknown,
  ctx: string,
): ReadonlyArray<boolean> {
  return expectArray(value, ctx, (v, itemCtx) => expectBoolean(v, itemCtx));
}

function expectArrayOfEnum<T extends string>(
  value: unknown,
  ctx: string,
  guard: (v: unknown, ctx: string) => T,
): ReadonlyArray<T> {
  return expectArray(value, ctx, (v, itemCtx) => guard(v, itemCtx));
}

function parseJsonValue(value: unknown, ctx: string): JsonValue {
  if (
    value === null ||
    typeof value === 'string' ||
    typeof value === 'number' ||
    typeof value === 'boolean'
  ) {
    return value;
  }

  if (Array.isArray(value)) {
    return value.map((v, i) =>
      parseJsonValue(v, `${ctx}[${i}]`)
    );
  }

  if (typeof value === 'object') {
    const o = value as Record<string, unknown>;
    const result: Record<string, JsonValue> = {};
    for (const [k, v] of Object.entries(o)) {
      result[k] = parseJsonValue(v, `${ctx}.${k}`);
    }
    return result;
  }

  throw new ContractParseError(`${ctx}: invalid JsonValue`);
}

function parseJsonObject(
  value: unknown,
  ctx: string,
): Readonly<Record<string, JsonValue>> {
  const parsed = parseJsonValue(value, ctx);

  if (
    parsed === null ||
    typeof parsed !== 'object' ||
    Array.isArray(parsed)
  ) {
    throw new ContractParseError(`${ctx}: expected JSON object`);
  }

  return parsed as Readonly<Record<string, JsonValue>>;
}


function expectOptionalString(value: unknown, ctx: string): string | null {
  if (value === null || value === undefined) {
    return null;
  }
  if (typeof value !== 'string') {
    throw new ContractParseError(`${ctx}: expected string or null`);
  }
  return value;
}


function expectOptionalBoolean(value: unknown, ctx: string): boolean | null {
  if (value === null || value === undefined) {
    return null;
  }
  if (typeof value !== 'boolean') {
    throw new ContractParseError(`${ctx}: expected boolean or null`);
  }
  return value;
}


function expectHealthStatus(value: unknown, ctx: string): HealthStatus {
  if (typeof value !== 'string' || (value !== 'OK' && value !== 'DEGRADED' && value !== 'FAILING')) {
    throw new ContractParseError(`${ctx}: invalid HealthStatus`);
  }
  return value as HealthStatus;
}


function expectSystemStatus(value: unknown, ctx: string): SystemStatus {
  if (typeof value !== 'string' || (value !== 'UP' && value !== 'DEGRADED' && value !== 'DOWN')) {
    throw new ContractParseError(`${ctx}: invalid SystemStatus`);
  }
  return value as SystemStatus;
}

export function parseApiVersionDescriptor(raw: unknown): ApiVersionDescriptor {
  const o = expectObject(raw, 'ApiVersionDescriptor');

  return {
    year: expectNumber(o['year'], 'year'),
    revision: expectNumber(o['revision'], 'revision'),
  };
}

export function parseAdminEndpoints(raw: unknown): AdminEndpoints {
  const o = expectObject(raw, 'AdminEndpoints');

  return {
    health: expectString(o['health'], 'health'),
    runtimeMetadata: expectString(o['runtime_metadata'], 'runtime_metadata'),
    configDiagnostics: expectString(o['config_diagnostics'], 'config_diagnostics'),
    observabilityDiagnostics: expectString(o['observability_diagnostics'], 'observability_diagnostics'),
  };
}

export function parseAdminHttpDescriptor(raw: unknown): AdminHttpDescriptor {
  const o = expectObject(raw, 'AdminHttpDescriptor');

  return {
    baseUrl: expectString(o['base_url'], 'base_url'),
    endpoints: parseAdminEndpoints(o['endpoints']),
  };
}

export function parseRuntimeMetadataResponse(raw: unknown): RuntimeMetadataResponse {
  const o = expectObject(raw, 'RuntimeMetadataResponse');

  return {
    status: expectSystemStatus(o['status'], 'status'),
    apiVersion: parseApiVersionDescriptor(o['api_version']),
    adminHttp: parseAdminHttpDescriptor(o['admin_http']),
  };
}

export function parseHealthResponse(raw: unknown): HealthResponse {
  const o = expectObject(raw, 'HealthResponse');

  return {
    status: expectHealthStatus(o['status'], 'status'),
  };
}

export function parseConfigReadyStateSnapshot(raw: unknown): ConfigReadyStateSnapshot {
  const o = expectObject(raw, 'ConfigReadyStateSnapshot');

  return {
    fsmStatus: expectString(o['fsm_status'], 'fsm_status'),
    env: expectOptionalRecordOfString(o['env'], 'env'),
    settings: o['settings'] === null || o['settings'] === undefined ? null : parseJsonObject(o['settings'], 'settings'),
    metadata: parseJsonObject(o['metadata'], 'metadata'),
  };
}

export function parseConfigDiagnosticsResponse(raw: unknown): ConfigDiagnosticsResponse {
  const o = expectObject(raw, 'ConfigDiagnosticsResponse');

  return {
    schemaVersion: expectString(o['schema_version'], 'schema_version'),
    isConsumable: expectBoolean(o['is_consumable'], 'is_consumable'),
    fingerprint: expectOptionalString(o['fingerprint'], 'fingerprint'),
    readyState: o['ready_state'] === null || o['ready_state'] === undefined ? null : parseConfigReadyStateSnapshot(o['ready_state']),
    loaderSnapshot: o['loader_snapshot'] === null || o['loader_snapshot'] === undefined ? null : parseJsonObject(o['loader_snapshot'], 'loader_snapshot'),
    reservedEnvKeys: expectRecordOfOptionalString(o['reserved_env_keys'], 'reserved_env_keys'),
    cacheMatchesParams: expectOptionalBoolean(o['cache_matches_params'], 'cache_matches_params'),
    hasValidCache: expectOptionalBoolean(o['has_valid_cache'], 'has_valid_cache'),
    error: expectOptionalString(o['error'], 'error'),
  };
}

export function parseObservabilityDiagnosticsResponse(raw: unknown): ObservabilityDiagnosticsResponse {
  const o = expectObject(raw, 'ObservabilityDiagnosticsResponse');

  return {
    pipelineUp: expectBoolean(o['pipeline_up'], 'pipeline_up'),
    loggingOk: expectBoolean(o['logging_ok'], 'logging_ok'),
    loggingSinkUp: expectBoolean(o['logging_sink_up'], 'logging_sink_up'),
    tracingOk: expectBoolean(o['tracing_ok'], 'tracing_ok'),
    tracingUp: expectBoolean(o['tracing_up'], 'tracing_up'),
    metricsHttpOk: expectBoolean(o['metrics_http_ok'], 'metrics_http_ok'),
    runId: expectOptionalString(o['run_id'], 'run_id'),
    correlationId: expectOptionalString(o['correlation_id'], 'correlation_id'),
    diagnostics: parseJsonObject(o['diagnostics'], 'diagnostics'),
  };
}
