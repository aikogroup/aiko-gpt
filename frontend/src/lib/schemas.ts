import { z } from "zod";

export const companySchema = z.object({
  company_name: z.string().min(1),
});

export const workflowStatusSchema = z.object({
  status: z.enum(["idle", "running", "paused", "completed", "error"]),
  waiting_for_validation: z.boolean().optional(),
  use_case_waiting_for_validation: z.boolean().optional(),
});

export type CompanyPayload = z.infer<typeof companySchema>;
export type WorkflowStatus = z.infer<typeof workflowStatusSchema>;


