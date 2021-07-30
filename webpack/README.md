#### 监控前端构建使用说明

###### 安装和更新前端依赖（`nodejs`最小依赖版本为`V10.13.0`）

```bash
cd webpack
npm ci
npm run install-build
```

如果您尚未安装过 `nodejs` [详细安装参见](https://nodejs.org/zh-cn/download/)

###### 本地开发模式

 * 本地启动

   ```bash
   # pc端本地开发模式
   npm run dev
   # 移动端本地开发模式
   npm run mobile:dev
   ```

* 前端环境变量配置

  1. 新建文件  `local.settings.js`

  2. 配置自定义内容 参考如下 [更多配置参见](https://webpack.docschina.org/configuration/dev-server/) 

     ```js
     const devProxyUrl = 'http://appdev.bktencent.com:9002'
     const devHost = 'appdev.bktencent.com'
     const loginHost = 'https://paas-dev.bktencent.com'
     const devPort = 7001
     module.exports = {
         port: devPort, // 启动端口
         host: devHost, // 启动host
         devProxyUrl, // 后端地址 用于代理转发api
         loginHost, // 登入地址
         proxy: { // api代理配置
             '/rest': { 
                 target: devProxyUrl,
                 changeOrigin: true,
                 secure: false,
                 toProxy: true
             }
     }
     
     ```

     

###### 生产构建

* 构建pc端和移动端

  ```bash
  npm run build
  ```

* 仅构建pc端

  ```bash
  npm run pc:build
  ```

* 仅构建移动端

  ```bash
  npm run mobile:build
  ```

###### 其他命令

  * 本地一键构建用于上云环境

    ```bash
    npm run prod
    ```

* 移动构建产品到 `static/`目录下

  ```bash
  npm run replace
  ```

* 分析构建产物组成

  ```bash
  # pc端生产环境构建产物分析
  npm run analyze
  # 移动端生产环境构建产物分析
  npm run analyze:mobile
  ```
#### help

  * 前端构建最小依赖node版本 V10.13.0
  * 编译过程中出现任何问题请联系 admin