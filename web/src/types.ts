export type Entity = {
  id: string;
  name: string;
  type: string;
  relations: Record<string, string[]>;
  extensions: { blender?: { evaluated_world?: number[][] } };
};
export type Change = {
  category: string;
  label: string;
  domain: string;
  before: unknown;
  after: unknown;
  compatible?: boolean;
  displacement?: {
    changed_vertices: number;
    max: number;
    mean_changed: number;
  };
};
export type RecordChange = {
  id: string;
  name: string;
  type: string;
  status: string;
  before: string | null;
  after: string | null;
  match: { confidence: string; evidence: string[] };
  changes: Change[];
};
export type Report = {
  before: { source: { name: string }; entities: Entity[] };
  after: { source: { name: string }; entities: Entity[] };
  diff: {
    records: RecordChange[];
    summary: Record<string, number>;
    coverage: { compared: string[]; not_compared: string[] };
    ambiguity: { before: string; after: string; evidence: string[] }[];
    context: { before: unknown; after: unknown };
  };
};
export type Mode = "A" | "B" | "Overlay" | "Compare";
