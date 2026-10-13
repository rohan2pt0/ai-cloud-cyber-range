{{/* Tier table: the one place that decides how big a tenant cell is. */}}
{{- define "tenant.tier" -}}
{{- $t := dict
  "small"  (dict "cpu" "2"  "mem" "4Gi"  "pods" "20"  "min" 1 "max" 3  "limCpu" "500m"  "limMem" "256Mi")
  "medium" (dict "cpu" "8"  "mem" "16Gi" "pods" "50"  "min" 2 "max" 8  "limCpu" "1"     "limMem" "512Mi")
  "large"  (dict "cpu" "32" "mem" "64Gi" "pods" "200" "min" 3 "max" 30 "limCpu" "2"     "limMem" "1Gi") -}}
{{- $sel := get $t .Values.tier -}}
{{- if not $sel -}}{{- fail (printf "tier must be small, medium or large (got %q)" .Values.tier) -}}{{- end -}}
{{- toYaml $sel -}}
{{- end -}}
{{- define "tenant.ns" -}}t-{{ .Values.tenant.id }}{{- end -}}
{{- define "tenant.labels" -}}
securax.io/tenant: {{ .Values.tenant.id | quote }}
securax.io/tier: {{ .Values.tier | quote }}
app.kubernetes.io/managed-by: argocd
{{- end -}}
