import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

import configs.config as config


class DashboardOverviewService:
    def __init__(self, db_manager):
        self.db = db_manager

    def get_overview(self):
        counts = self._collect_counts()
        return {
            "counts": counts,
            "assets": {
                "files": counts["files"],
                "knowledge_bases": counts["knowledge_bases"],
                "knowledge_packs": counts["knowledge_packs"],
            },
            "vllm_services": self._collect_vllm_services(),
            "gpu_memory": self._collect_gpu_memory(),
        }

    def _collect_counts(self):
        return {
            "qa_sessions": len(self.db.get_all_sessions("qa_history")),
            "rlhf_sessions": len(self.db.get_all_sessions("rlhf_history")),
            "files": len(self.db.list_files()),
            "knowledge_bases": len(self.db.list_knowledge_bases()),
            "knowledge_packs": len(self.db.list_knowledge_base_groups()),
        }

    def _collect_vllm_services(self):
        return [self._probe_service(service) for service in config.vllm_services]

    def _probe_service(self, service: dict):
        api_base = service["api_base"].rstrip("/")
        service_root = self._service_root(api_base)
        health_url = f"{service_root}/health"
        models_url = f"{api_base}/models"

        health_probe = self._request_url(health_url, timeout=1.2)
        if health_probe["ok"]:
            return {
                "id": service["id"],
                "label": service["label"],
                "service_type": service["service_type"],
                "served_model": service["served_model"],
                "api_base": service["api_base"],
                "status": "online",
                "latency_ms": health_probe["latency_ms"],
                "message": "健康检查可达。",
            }

        fallback_probe = self._request_url(
            models_url,
            timeout=1.5,
            headers={"Authorization": f"Bearer {service['api_key']}"},
        )
        if fallback_probe["ok"]:
            return {
                "id": service["id"],
                "label": service["label"],
                "service_type": service["service_type"],
                "served_model": service["served_model"],
                "api_base": service["api_base"],
                "status": "degraded",
                "latency_ms": fallback_probe["latency_ms"],
                "message": "健康检查失败，但 OpenAI 兼容接口可达。",
            }

        return {
            "id": service["id"],
            "label": service["label"],
            "service_type": service["service_type"],
            "served_model": service["served_model"],
            "api_base": service["api_base"],
            "status": "offline",
            "latency_ms": None,
            "message": health_probe["message"] or fallback_probe["message"] or "服务不可达。",
        }

    def _service_root(self, api_base: str):
        parsed = urllib.parse.urlparse(api_base)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _request_url(self, url: str, timeout: float, headers: dict | None = None):
        started = time.perf_counter()
        request = urllib.request.Request(url, headers=headers or {})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                latency_ms = int((time.perf_counter() - started) * 1000)
                if 200 <= response.status < 300:
                    return {"ok": True, "latency_ms": latency_ms, "message": ""}
                return {
                    "ok": False,
                    "latency_ms": latency_ms,
                    "message": f"HTTP {response.status}",
                }
        except urllib.error.HTTPError as exc:
            return {"ok": False, "latency_ms": None, "message": f"HTTP {exc.code}"}
        except Exception as exc:
            return {"ok": False, "latency_ms": None, "message": str(exc)}

    def _collect_gpu_memory(self):
        command = [
            "nvidia-smi",
            "--query-gpu=index,name,memory.used,memory.total,utilization.gpu",
            "--format=csv,noheader,nounits",
        ]
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=4,
                check=True,
                creationflags=creationflags,
            )
        except Exception:
            return {
                "status": "unavailable",
                "total_used_mb": 0,
                "total_mb": 0,
                "utilization_percent": 0,
                "gpus": [],
            }

        rows = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        gpus = []
        for row in rows:
            parts = [item.strip() for item in row.split(",")]
            if len(parts) != 5:
                continue
            try:
                gpu = {
                    "index": int(parts[0]),
                    "name": parts[1],
                    "memory_used_mb": int(parts[2]),
                    "memory_total_mb": int(parts[3]),
                    "utilization_gpu_percent": int(parts[4]),
                }
            except ValueError:
                continue
            gpus.append(gpu)

        if not gpus:
            return {
                "status": "unavailable",
                "total_used_mb": 0,
                "total_mb": 0,
                "utilization_percent": 0,
                "gpus": [],
            }

        total_used_mb = sum(gpu["memory_used_mb"] for gpu in gpus)
        total_mb = sum(gpu["memory_total_mb"] for gpu in gpus)
        utilization_percent = round(
            sum(gpu["utilization_gpu_percent"] for gpu in gpus) / max(len(gpus), 1)
        )
        return {
            "status": "ok",
            "total_used_mb": total_used_mb,
            "total_mb": total_mb,
            "utilization_percent": utilization_percent,
            "gpus": gpus,
        }
