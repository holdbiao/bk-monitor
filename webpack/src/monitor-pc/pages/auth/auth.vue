<template>
  <div class="auth" v-monitor-loading="{ 'isLoading': pageLoading }">
    <bk-table
      @header-dragend="handleHeaderDrag"
      :cell-class-name="setCellClass"
      :data="tableData">
      <bk-table-column :label="$t('用户组')" prop="role_display"></bk-table-column>
      <bk-table-column :label="$t('人员列表(同步CMDB)')" prop="userList" min-width="250" class-name="uesr-td" v-slot="scope">
        <div class="user-list-wrapper" :ref="`userList-${scope.$index}`">
          {{scope.row.user_list || '--'}}
        </div>
      </bk-table-column>
      <bk-table-column :label="$t('权限类型')" v-slot="scope">
        <div class="auth-list">
          <span class="auth-name">
            {{authMap[scope.row.permission] ? authMap[scope.row.permission].join('、') : '--'}}
          </span>
          <!-- <div class="icon-wrapper" @click="handleShowDialog(scope.row)">
                        <i class="icon-monitor icon-bianji"></i>
                    </div> -->
        </div>
      </bk-table-column>
      <bk-table-column :label="$t('最后编辑人')" v-slot="scope">
        <div>{{scope.row.update_user}}</div>
      </bk-table-column>
      <bk-table-column :label="$t('编辑时间')" v-slot="scope" width="180">
        <div>{{scope.row.update_time}}</div>
      </bk-table-column>
      <bk-table-column width="100" :label="$t('操作')" v-slot="scope">
        <div class="col-operator" @click="handleShowDialog(scope.row)"> {{ $t('编辑') }} </div>
      </bk-table-column>
    </bk-table>
    <bk-dialog
      :width="480"
      :value="showDialog"
      render-directive="show"
      :mask-close="false"
      header-position="left" :title="$t('权限变更')"
      :auto-close="false"
      @confirm="handleUpdateAuth"
      @after-leave="handleAfterLeave">
      <div>
        <p class="description">{{ $t('本次是对') }} "{{userGroup ? userGroup.role_display : ''}}" {{ $t('用户组的权限变更') }}</p>
        <div class="checkbox-group">
          <bk-checkbox-group v-model="auths">
            <bk-checkbox value="r"> {{ $t('查询') }} </bk-checkbox>
            <bk-checkbox value="w"> {{ $t('变更')}} </bk-checkbox>
          </bk-checkbox-group>
        </div>
      </div>
    </bk-dialog>
  </div>
</template>
<script>
import { getUserInfo, saveRolePermission } from '../../../monitor-api/modules/config'
export default {
  name: 'Auth',
  data() {
    return {
      pageLoading: true,
      showDialog: false,
      userGroup: null,
      auths: [],
      authMap: {
        r: [this.$t('查询')],
        w: [this.$t('查询'), this.$t('变更')]
      },
      tableData: []
    }
  },
  created() {
    this.hanldeGetUserInfo()
  },
  methods: {
    /**
     * 计算人员列表的dom高度
     */
    calculateListHeight() {
      const timer = setTimeout(() => {
        this.tableData.forEach((item, index) => {
          const el = this.$refs[`userList-${index}`]
          item.expanded = el.clientHeight > 20
          clearTimeout(timer)
        })
      }, 100)
    },
    setCellClass(obj) {
      return obj.row.expanded && obj.columnIndex !== 1 ? 'expanded' : ''
    },
    handleHeaderDrag() {
      this.calculateListHeight()
    },
    /**
             * @description: 显示dialog
             * @param {Object} obj
             * @return:
             */
    handleShowDialog(obj) {
      this.userGroup = obj
      if (obj.permission) {
        this.auths = obj.permission === 'w' ? ['r', 'w'] : ['r']
      } else {
        this.auths = []
      }
      this.showDialog = true
    },
    handleAfterLeave() {
      this.showDialog = false
    },
    /**
     * @description: 更新权限
     * @param {String} role
     * @param {String} permission
     * @return:
     */
    handleUpdateAuth() {
      this.showDialog = false
      this.pageLoading = true
      let auth = null
      const params = { role: this.userGroup.role }
      if (this.auths.length) {
        auth = this.auths.includes('w') ? 'w' : 'r'
        params.permission = auth
      }
      saveRolePermission(params).then(() => {
        this.userGroup.permission = auth
        this.hanldeGetUserInfo()
        this.$bkMessage({
          theme: 'success',
          message: this.$t('修改权限成功')
        })
      })
        .catch(() => {
          this.pageLoading = false
        })
    },
    hanldeGetUserInfo() {
      getUserInfo().then((res) => {
        this.tableData = res.data.map((item) => {
          item.expanded = false
          return item
        })
        this.$nextTick(() => {
          this.calculateListHeight()
          this.pageLoading = false
        })
      })
        .catch(() => {
          this.pageLoading = false
        })
    }
  }
}
</script>
<style lang='scss' scoped>
.auth {
  min-height: calc(100vh - 80px);
  /deep/ .expanded {
    .cell {
      height: 100%;
      padding-top: 7px;
    }
  }
  /deep/ .bk-table {
    .bk-table-body-wrapper {
      .uesr-td {
        .cell {
          -webkit-line-clamp: unset;
          padding: 7px 15px;
        }
      }
    }

  }
  .auth-list {
    display: flex;
    .auth-name {
      margin-right: 10px;
    }
    .icon-wrapper {
      position: relative;
      width: 24px;
    }
    // .icon-monitor {
    //     display: none;
    //     position: absolute;
    //     top: -5px;
    //     left: -10px;
    //     font-size: 24px;
    // }
    // &:hover {
    //     .icon-monitor {
    //         display: inline-block;
    //         cursor: pointer;
    //         color: #3A84FF;
    //     }
    // }
  }
  .col-operator {
    color: #3a84ff;
    cursor: pointer;
  }
  .description {
    font-size: 12px;
    margin-top: 0;
    margin-bottom: 13px;
  }
  /deep/ .bk-dialog-wrapper {
    .bk-dialog-body {
      padding-top: 8px;
    }
    .bk-form-checkbox {
      margin-right: 50px;
    }
    .header-on-left {
      padding-bottom: 0;
    }
    .checkbox-group {
      position: relative;
      .error-message {
        position: absolute;
        top: 22px;
        font-size: 12px;
        color: #f56c6c;
      }
    }
    .footer-wrapper {
      .bk-default {
        margin-left: 10px;
      }
    }
  }
}
</style>
