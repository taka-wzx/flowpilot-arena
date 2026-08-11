# Aliyun ACK deployment runbook

This runbook deploys only the deterministic W16 Web demo to an existing,
explicitly authorized Alibaba Cloud ACK cluster. It does not create a cluster,
VPC, EIP, load balancer, DNS record, certificate, database, identity provider,
or external model/provider integration. The chart remains namespace-scoped,
digest-only, default-deny, non-root, read-only, and zero-real-call.

## Required local state

Obtain a temporary least-privilege kubeconfig from the ACK console and keep it
outside this repository. Alibaba Cloud documents the console path and the
temporary-versus-long-term credential trade-off in its
[ACK kubeconfig guide](https://www.alibabacloud.com/help/en/ack/ack-managed-and-ack-dedicated/user-guide/obtain-the-kubeconfig-file-of-a-cluster-and-use-kubectl-to-connect-to-the-cluster).
Never paste the kubeconfig, token, client key, or certificate into Git, an
issue, a workflow input, or command output captured as release evidence.

Set the following values in the current PowerShell process:

~~~powershell
$env:KUBECONFIG = 'C:\secure\flowpilot-ack-temporary.kubeconfig'
$Context = '<exact-authorized-ack-context>'
$Namespace = 'flowpilot-w16'
$ControlWebDigest = 'sha256:<64-hex-control-web-digest>'
$SandboxWebDigest = 'sha256:<64-hex-sandbox-web-digest>'
~~~

The context and both digests must be concrete before continuing. Verify the
target without printing credential material:

~~~powershell
kubectl --context $Context config current-context
kubectl --context $Context cluster-info
kubectl --context $Context auth can-i create namespaces
kubectl --context $Context auth can-i create deployments --namespace $Namespace
~~~

Stop if the context is not the authorized ACK target, connectivity fails, or
the required namespace permissions are denied.

## Verify image attestations before deployment

Authenticate `gh` and Docker locally without persisting a token in the
repository, then verify the exact immutable image subjects:

~~~powershell
gh auth token | docker login ghcr.io --username taka-wzx --password-stdin
gh attestation verify "oci://ghcr.io/taka-wzx/flowpilot-arena-control-web@$ControlWebDigest" --repo taka-wzx/flowpilot-arena --predicate-type https://spdx.dev/Document/v2.3
gh attestation verify "oci://ghcr.io/taka-wzx/flowpilot-arena-sandbox-web@$SandboxWebDigest" --repo taka-wzx/flowpilot-arena --predicate-type https://spdx.dev/Document/v2.3
~~~

## Namespace-scoped install and verification

The Web-only sandbox needs the same DNS-only `sandbox-api` ClusterIP stub used
by the verified kind lifecycle. The stub has no endpoints and grants no API
capability.

~~~powershell
kubectl --context $Context create namespace $Namespace
kubectl --context $Context --namespace $Namespace create service clusterip sandbox-api --tcp=8001:8001

helm lint deploy/helm/flowpilot-arena --strict `
  --set components.controlWeb.enabled=true `
  --set-string components.controlWeb.image.repository=ghcr.io/taka-wzx/flowpilot-arena-control-web `
  --set-string components.controlWeb.image.digest=$ControlWebDigest `
  --set components.sandboxWeb.enabled=true `
  --set-string components.sandboxWeb.image.repository=ghcr.io/taka-wzx/flowpilot-arena-sandbox-web `
  --set-string components.sandboxWeb.image.digest=$SandboxWebDigest

helm upgrade --install flowpilot-w16 deploy/helm/flowpilot-arena `
  --kube-context $Context `
  --namespace $Namespace `
  --wait --timeout 5m `
  --set components.controlWeb.enabled=true `
  --set-string components.controlWeb.image.repository=ghcr.io/taka-wzx/flowpilot-arena-control-web `
  --set-string components.controlWeb.image.digest=$ControlWebDigest `
  --set components.sandboxWeb.enabled=true `
  --set-string components.sandboxWeb.image.repository=ghcr.io/taka-wzx/flowpilot-arena-sandbox-web `
  --set-string components.sandboxWeb.image.digest=$SandboxWebDigest

kubectl --context $Context --namespace $Namespace rollout status deployment/flowpilot-w16-flowpilot-arena-control-web --timeout=180s
kubectl --context $Context --namespace $Namespace rollout status deployment/flowpilot-w16-flowpilot-arena-sandbox-web --timeout=180s
kubectl --context $Context --namespace $Namespace get pods,services,networkpolicies
~~~

Use a local port-forward for the bounded verification; this does not create a
public endpoint:

~~~powershell
kubectl --context $Context --namespace $Namespace port-forward service/flowpilot-w16-flowpilot-arena-control-web 18080:80
~~~

From a second terminal, request `http://127.0.0.1:18080/`. Record the context
name, Kubernetes version, namespace, immutable digests, rollout status, and
HTTP status only. Do not capture kubeconfig content, API server tokens, client
certificates, public IPs, account IDs, or unrelated namespaces.

## Cleanup

When the authorized demo lifetime ends:

~~~powershell
helm uninstall flowpilot-w16 --kube-context $Context --namespace $Namespace --wait
kubectl --context $Context --namespace $Namespace delete service sandbox-api
kubectl --context $Context delete namespace $Namespace --wait=true
~~~

Public ingress, DNS, and TLS remain separate operations. Execute them only
when the exact authorized domain, DNS zone, certificate source, exposure
policy, budget, and deletion deadline are available in the active session.
