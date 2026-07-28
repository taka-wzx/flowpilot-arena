export interface Employee {
  id: number;
  first_name: string;
  last_name: string;
  work_email: string;
  department: string;
  job_title: string;
  location: string;
  start_date: string;
  status: "confirmed" | "transferred" | "disabled";
  created_at: string;
}

export interface Ticket {
  id: number;
  employee_id: number;
  title: string;
  status: "open" | "closed";
  created_at: string;
}

export interface Account {
  id: number;
  employee_id: number;
  username: string;
  role: "employee";
  status: "active" | "revoked";
  created_at: string;
}

export interface Asset {
  id: number;
  employee_id: number;
  asset_tag: string;
  device_type: "laptop";
  model: string;
  status: "assigned" | "released";
  created_at: string;
}

export interface Mailbox {
  id: number;
  employee_id: number;
  address: string;
  status: "active" | "disabled";
  created_at: string;
}
