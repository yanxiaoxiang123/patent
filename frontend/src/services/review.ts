import api from "./api";
import type {
  ReviewRequest,
  FormalCheckResult,
  LogicCheckResult,
  ApiResponse,
} from "@/types";

export const performFormalCheck = async (
  text: string,
): Promise<FormalCheckResult> => {
  const response = await api.post("/test/ollama/generate", {
    text,
    check_type: "formal",
  });
  return response.result;
};

export const performLogicCheck = async (
  claims: string,
  description: string,
): Promise<string> => {
  const response = await api.post("/test/ollama/logic-check-sample", {
    claims,
    description,
  });
  return response.analysis;
};

export const getFormalCheckSample = async (): Promise<FormalCheckResult> => {
  const response = await api.post("/test/ollama/formal-check-sample");
  return response.result;
};
