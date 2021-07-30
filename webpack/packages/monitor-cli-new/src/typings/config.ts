export interface ServiceConfig {
  mobile: boolean;
  analyze: boolean;
  email: boolean;
  env: any;
  dist: string;
  appDir: string;
  appIndex: string;
  appIndexHtml: string;
}

export interface BundleOptions {
  production: boolean;
  mobile: boolean;
  analyze?: boolean;
  email?: boolean;
}
