{{- define "flowpilot.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "flowpilot.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "flowpilot.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "flowpilot.labels" -}}
app.kubernetes.io/name: {{ include "flowpilot.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | quote }}
{{- end -}}

{{- define "flowpilot.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "flowpilot.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}
