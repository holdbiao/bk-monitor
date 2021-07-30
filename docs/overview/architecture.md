#蓝鲸监控平台(BK-MONITOR)架构

![产品架构图](../resource/img/architecture.png)

从下至上依次介绍:

- 管控平台：蓝鲸 PaaS 的优势，可以满足不同的云区域的需求，满足文件、命令、数据的基本需求。并且整个监控平台也是建立在蓝鲸的 PaaS 平台之上
- 依赖服务：是在蓝鲸工作的过程中需要依赖的蓝鲸 SaaS。分为强依赖缺一不可，增强型有配套功能会更加的强大
- 监控服务层：监控的核心服务能力，每个服务都可以独立配置和复用，满足上层监控场景和需求的复杂需求。每块能力都是可以不断的补充
- 监控场景：针对不同的监控场景有更加专业的场景来满足用户的问题定位。当前主要是主机监控和服务拨测
- 用户层：用户可以直接接触到监控的一些途径