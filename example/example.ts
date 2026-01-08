export interface Config {
  name: string;
  retries?: number;
}

export function greet(c: Config): string {
  return `Hi ${c.name}`;
}
