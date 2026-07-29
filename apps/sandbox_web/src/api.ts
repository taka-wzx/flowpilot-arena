export async function listRecords<RecordType>(path: string): Promise<RecordType[]> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Unable to load records (${response.status})`);
  }
  return (await response.json()) as RecordType[];
}

export async function createRecord<RecordType>(
  path: string,
  payload: Record<string, unknown>,
): Promise<RecordType> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new Error(body.detail ?? `Unable to create record (${response.status})`);
  }
  return (await response.json()) as RecordType;
}

export async function updateRecord<RecordType>(
  path: string,
  payload: Record<string, unknown>,
): Promise<RecordType> {
  const response = await fetch(path, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new Error(body.detail ?? `Unable to update record (${response.status})`);
  }
  return (await response.json()) as RecordType;
}
