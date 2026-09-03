declare module "*.sql" {
    const content: string;
    export default content;
}

declare module "*.toml" {
    const content: Record<string, any>;
    export default content;
}
