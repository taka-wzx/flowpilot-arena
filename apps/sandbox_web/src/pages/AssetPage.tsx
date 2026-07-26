import { useCallback, useEffect, useState, type FormEvent } from "react";

import { createRecord, listRecords } from "../api";
import type { Asset } from "../types";

const path = "/api/assets/devices";

export function AssetPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [error, setError] = useState("");
  const refresh = useCallback(async () => {
    try {
      setAssets(await listRecords<Asset>(path));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load assets");
    }
  }, []);
  useEffect(() => {
    void listRecords<Asset>(path)
      .then(setAssets)
      .catch((reason: Error) => setError(reason.message));
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const form = event.currentTarget;
    const data = new FormData(form);
    try {
      await createRecord<Asset>(path, {
        employee_id: Number(data.get("employee_id")),
        asset_tag: data.get("asset_tag"),
        model: data.get("model"),
      });
      form.reset();
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to assign asset");
    }
  }

  return (
    <section>
      <div className="section-heading"><div><p className="module-code">04 / ASSET</p><h2>Device assignments</h2></div><p>Assign one synthetic laptop tag beginning with SYN-.</p></div>
      <form onSubmit={submit}>
        <label>Employee ID<input name="employee_id" type="number" min="1" required /></label>
        <label>Asset tag<input name="asset_tag" pattern="SYN-[A-Z0-9-]+" required /></label>
        <label>Model<input name="model" required /></label>
        <button type="submit">Assign laptop</button>
      </form>
      {error && <p role="alert" className="error">{error}</p>}
      <div className="records">{assets.length === 0 ? <p>No assigned devices yet.</p> : assets.map((asset) => (
        <article key={asset.id}><strong>#{asset.id} · {asset.asset_tag}</strong><span>Employee #{asset.employee_id} · {asset.model}</span><em>{asset.status}</em></article>
      ))}</div>
    </section>
  );
}
