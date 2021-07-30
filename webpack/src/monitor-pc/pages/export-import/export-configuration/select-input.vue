<template>
  <div class="select-input">
    <!-- 左边主选框 -->
    <bk-select v-model="value" class="all-select" @change="handlemainBoxSwitch" :clearable="false" :z-index="10" style="width: 160px">
      <bk-option v-for="option in list"
                 :key="option.id"
                 :id="option.id"
                 :name="option.name">
      </bk-option>
    </bk-select>
    <!-- 选择：全部 搜索框 -->
    <bk-input :clearable="true" v-show="value === 1"
              v-model="allFind.value" :placeholder="$t('采集名称/策略名称')"
              :right-icon="'bk-icon icon-search'"
              @change="handleSearch"
              @clear="handlemainBoxSwitch"
    ></bk-input>
    <!-- 选择：节点 节点树 -->
    <select-input-template :value="selectNode.value" :placeholder="$t('业务/集群/节点')" v-show="value === 2" @clear="handlemainBoxSwitch" ref="node">
      <div class="node-padding" v-if="treeData.length">
        <bk-big-tree
          :data="treeData">
          <template slot-scope="scope">
            <div class="tree-data" @mouseenter="handleNodeEnter(scope.node.id)" @mouseleave="handleNodeLeave">
              <div :class="{ 'choice': selectNode.id === scope.node.id }">{{ scope.node.name }}</div>
              <div class="selection-data choice" v-show="selectNode.hoverId === scope.node.id" @click="handleChoiceNode(scope.node)"> {{ $t('选取') }} </div>
            </div>
          </template>
        </bk-big-tree>
      </div>
    </select-input-template>
    <!-- 选择：服务分类 二级选框 -->
    <select-input-template :value="serverSearch.value" v-show="value === 3" @clear="handlemainBoxSwitch" ref="server">
      <div class="server-content" v-if="serviceCategory.length">
        <div class="content-left">
          <div v-for="(item, index) in serviceCategory" :key="index"
               class="content-item"
               :class="{ 'click-item': serverSearch.firstIndex === index }"
               @mouseenter="handleFirstServerMove(index, item)">
            {{ item.name }}
            <i class="bk-select-angle bk-icon icon-angle-right"></i>
          </div>
        </div>
        <div class="content-right" v-show="serverSearch.children.length">
          <div v-for="(item, index) in serverSearch.children" :key="index"
               class="content-item"
               :class="{ 'click-item': serverSearch.secondIndex === index && serverSearch.copyFirstIndex === serverSearch.firstIndex }"
               @click="handleServerClick(index, item)">
            {{ item.name }}
          </div>
        </div>
      </div>
    </select-input-template>
    <!-- 选择：数据对象 二级下拉框 -->
    <bk-select v-show="value === 4" class="data-obj"
               v-model="dataObj.value"
               :scroll-height="427"
               @change="handleDataObjChange"
               @clear="handlemainBoxSwitch">
      <bk-option-group
        v-for="(group, index) in dataObject"
        :name="group.name"
        :key="index">
        <bk-option v-for="(option, groupIndex) in group.children"
                   :key="groupIndex"
                   :id="option.id"
                   :name="option.name">
        </bk-option>
      </bk-option-group>
    </bk-select>
  </div>
</template>

<script>
import { debounce } from 'throttle-debounce'
import selectInputTemplate from './select-input-template'
import { mapActions, mapGetters } from 'vuex'
export default {
  name: 'select-input',
  components: {
    selectInputTemplate
  },
  props: {
    parentLoading: Boolean,
    defaultValue: {
      type: Object,
      default: () => ({ value: 1, searchValue: '' })
    }
  },
  data() {
    return {
      value: 1,
      list: [
        { id: 1, name: this.$t('全部') },
        { id: 2, name: this.$t('节点') },
        { id: 3, name: this.$t('服务分类') },
        { id: 4, name: this.$t('数据对象') }
      ],
      // 全部
      allFind: {
        value: '',
        handleSearch() {}
      },
      // 数据对象
      dataObj: {
        value: ''
      },
      // 节点
      selectNode: {
        id: 0,
        hoverId: -1,
        value: ''
      },
      // 服务分类
      serverSearch: {
        children: [],
        firstIndex: -1,
        firstValue: '',
        secondIndex: -1,
        value: ''
      }
    }
  },
  computed: {
    ...mapGetters('common', ['treeData', 'dataObject', 'serviceCategory'])
  },
  async created() {
    this.handleSearch = debounce(500, this.handleFindAll)
    await this.getSelectData()
    this.handleRouterJump()
  },
  methods: {
    ...mapActions('export', ['getAllExportList']),
    ...mapActions('common', ['getTopoTree', 'getDataObject', 'getServiceCategory']),
    async getSelectData() {
      // 获取动态拓扑树选择框的数据
      if (!this.treeData.length) {
        await this.getTopoTree().catch(() => {
          this.$bkMessage({ theme: 'error', message: this.$t('节点拓扑树请求失败') })
        })
      }
      // 获取数据对象选择框的数据
      if (!this.dataObject.length) {
        await this.getDataObject().catch(() => {
          this.$bkMessage({ theme: 'error', message: this.$t('数据对象分类请求失败') })
        })
      }
      // 获取服务分类选择框的数据
      if (!this.serviceCategory.length) {
        await this.getServiceCategory().catch(() => {
          this.$bkMessage({ theme: 'error', message: this.$t('服务分类请求失败') })
        })
      }
    },
    // 主选框切换事件 clear-icon事件
    handlemainBoxSwitch() {
      if (this.parentLoading) return
      this.selectNode.id = -1
      if (this.allFind.value || this.dataObj.value || this.selectNode.value || this.serverSearch.value) {
        this.getQueryTableData()
      }
      this.allFind.value = ''
      this.dataObj.value = ''
      this.selectNode.value = ''
      this.serverSearch.value = ''
    },
    // 全部搜索事件
    handleFindAll(v) {
      this.getQueryTableData({ search_value: v })
    },
    // 节点搜索事件
    handleChoiceNode(node) {
      const nameArr = node.parents.map(item => item.data.name)
      nameArr.push(node.name)
      this.selectNode.show = false
      this.selectNode.value = nameArr.join('/')
      this.selectNode.id = this.selectNode.hoverId
      this.getQueryTableData({ cmdb_node: `${node.data.bk_obj_id}|${node.data.bk_inst_id}` })
      this.$refs.node.handleSelectBlur()
    },
    // 服务分类一级选择mousehover事件
    handleFirstServerMove(index, item) {
      this.serverSearch.children = item.children
      this.serverSearch.firstIndex = index
      this.serverSearch.firstValue = item.name
    },
    // 服务分类搜索事件
    handleServerClick(index, item) {
      this.serverSearch.value = `${this.serverSearch.firstValue}：${item.name}`
      this.serverSearch.secondIndex = index
      this.serverSearch.copyFirstIndex = this.serverSearch.firstIndex
      this.serverSearch.show = false
      this.getQueryTableData({ service_category_id: item.id })
      this.$refs.server.handleSelectBlur()
    },
    // 数据对象搜索事件
    handleDataObjChange(newV) {
      this.getQueryTableData({ label: newV })
    },
    // 节点划入高亮事件
    handleNodeEnter(id) {
      this.selectNode.hoverId = id
    },
    // 节点划出事件
    handleNodeLeave() {
      this.selectNode.hoverId = -1
    },
    // 处理其他路由跳转导出页面
    handleRouterJump() {
      const { defaultValue } = this
      this.value = defaultValue.value
      if (defaultValue.routeName === 'service-classify') {
        this.serverSearch.firstValue = defaultValue.serverFirst
        const el = this.serviceCategory.some((item) => {
          if (item.name === defaultValue.serverFirst) {
            const index = item.children.findIndex(child => child.name === defaultValue.serverSecond)
            index > -1 && this.handleServerClick(index, item.children[index])
            return true
          }
          return false
        })
        if (!el) {
          this.$emit('change-table-loading', false)
        }
      }
    },
    // 搜索接口
    async getQueryTableData(params = {}) {
      this.$emit('change-table-loading', true)
      const data = await this.getAllExportList(params)
      this.$emit('select-data', data)
      this.$emit('change-table-loading', false)
    }
  }
}
</script>

<style lang="scss" scoped>
    .select-input {
      margin-bottom: 20px;
      display: flex;
      width: 506px;
      .all-select {
        background: #fff;
        min-width: 120px;
        margin-right: 6px;
      }
      .data-obj {
        width: 380px;
        background: #fff;
      }
      .node-padding {
        width: 380px;
        padding-top: 6px;
        overflow: scroll;
        max-height: 760px;
      }
      .server-content {
        display: flex;
        .content-left {
          background: #fff;
          width: 190px;
          border-right: 1px solid #dcdee5;
          padding-top: 6px;

        }
        .content-right {
          background: #fff;
          width: 190px;
          padding-top: 6px;
        }
        .content-item {
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 10px 0 15px;
          &:hover {
            background: #e1ecff;
            color: #3a84ff;
            cursor: pointer;
          }
        }
        .click-item {
          background: #fafbfd;
          color: #3a84ff;
        }
      }

    }
    .tree-data {
      display: flex;
      align-items: center;
      justify-content: space-between;
      .selection-data {
        margin-right: 11px;
      }
      .choice {
        color: #3a84ff;
      }
    }
    /deep/ .bk-big-tree-node {
      padding-left: calc(var(--level) * 30px + 20px);
    }
</style>
