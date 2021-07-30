/* eslint-disable max-len */
import * as exOrInAuth from '../../pages/export-import/authority-map'
import { RouteConfig } from 'vue-router'
const ImportExport = () => import(/* webpackChunkName: 'ImportExport' */'@page/export-import/export-import.vue')
const ExportConfiguration = () => import(/* webpackChunkName: 'ExportConfiguration' */'@page/export-import/export-configuration/export-configuration.vue')
const ImportConfigurationUpload = () => import(/* webpackChunkName: 'ImportConfigurationUpload' */'@page/export-import/import-configuration/import-configuration-upload.vue')
const ImportConfiguration = () => import(/* webpackChunkName: 'ImportConfiguration' */'@page/export-import/import-configuration/import-configuration.vue')
const ImportConfigurationImporting = () => import(/* webpackChunkName: 'ImportConfigurationImporting' */'@page/export-import/import-configuration/import-configuration-importing.vue')
const ImportConfigurationHistory = () => import(/* webpackChunkName: 'ImportConfigurationHistory' */'@page/export-import/import-configuration/import-configuration-history.vue')
const ImportConfigurationTarget = () => import(/* webpackChunkName: 'ImportConfigurationTarget' */'@page/export-import/import-configuration/import-configuration-target.vue')
export default [
  {
    path: '/export-import',
    name: 'export-import',
    components: {
      noCache: ImportExport
    },
    meta: {
      title: '导入/导出',
      navId: 'export-import',
      authority: {
        map: exOrInAuth,
        page: exOrInAuth.VIEW_AUTH
      }
    }
  },
  {
    path: '/export-import/export-configuration',
    name: 'export-configuration',
    components: {
      noCache: ExportConfiguration
    },
    meta: {
      title: '导出配置',
      navId: 'export-import',
      needBack: true,
      authority: {
        map: exOrInAuth,
        page: exOrInAuth.MANAGE_EXPORT_CONFIG
      }
    }
  },
  {
    path: '/export-import/import-upload',
    name: 'import-configuration-upload',
    components: {
      noCache: ImportConfigurationUpload
    },
    meta: {
      title: '导入配置',
      navId: 'export-import',
      needBack: true,
      authority: {
        map: exOrInAuth,
        page: exOrInAuth.MANAGE_IMPORT_CONFIG
      }
    }
  },
  {
    path: '/export-import/import-config',
    name: 'import-configuration',
    props: {
      noCache: true
    },
    components: {
      noCache: ImportConfiguration
    },
    meta: {
      title: '导入配置',
      navId: 'export-import',
      needBack: true,
      authority: {
        map: exOrInAuth,
        page: exOrInAuth.MANAGE_IMPORT_CONFIG
      }
    }
  },
  {
    path: '/export-import/import-config-detail/:id',
    name: 'import-configuration-importing',
    props: true,
    component: ImportConfigurationImporting,
    meta: {
      title: '导入配置',
      navId: 'export-import',
      needBack: true,
      authority: {
        map: exOrInAuth,
        page: exOrInAuth.MANAGE_IMPORT_CONFIG
      }
    }
  },
  {
    path: '/export-import/config-history',
    name: 'import-configuration-history',
    components: {
      noCache: ImportConfigurationHistory
    },
    meta: {
      title: '导入历史',
      navId: 'export-import',
      needBack: true,
      authority: {
        map: exOrInAuth,
        page: exOrInAuth.MANAGE_IMPORT_CONFIG
      }
    }
  },
  {
    path: '/export-import/config-target',
    name: 'import-configuration-target',
    props: {
      noCache: true
    },
    components: {
      noCache: ImportConfigurationTarget
    },
    meta: {
      title: '统一添加策略目标',
      navId: 'export-import',
      needBack: true,
      authority: {
        map: exOrInAuth,
        page: exOrInAuth.MANAGE_IMPORT_CONFIG
      }
    }
  }
] as RouteConfig[]
