<template>
  <div class="shell-side-notice">
    <div class="notice-title"> {{ $t('上报格式说明') }} </div>
    <div class="notice-content">
      <div class="notice-content-desc"> {{ $t('数据格式需遵循') }} <span @click="handleGotoPage">{{ $t('Prometheus Metrics 标准格式') }}</span>，{{ $t('如下') }} </div>
      <div class="notice-content-code">
        metric_name{label_name="lable_value"} metric_value timestamp
      </div>
    </div>
    <div class="notice-table">
      <table>
        <thead>
          <tr>
            <th style="width: 110px">
              metric_name
            </th>
            <th style="width: 200px"> {{ $t('指标名称') }} </th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              label_name
            </td>
            <td>
              {{ $t('维度名称') }}
            </td>
          </tr>
          <tr>
            <td>
              label_value
            </td>
            <td>
              {{ $t('维度值,字符串 ；可选') }}
            </td>
          </tr>
          <tr>
            <td>
              metric_value
            </td>
            <td> {{ $t('指标值,数值 ；') }} </td>
          </tr>
          <tr>
            <td>
              timestamp
            </td>
            <td> {{ $t('时间戳(ms)；可选') }} </td>
          </tr>
          <tr>
            <td>
              {{ $t('一个指标一行') }}
            </td>

          </tr>
        </tbody>
      </table>
    </div>
    <div class="notice-title"> {{ $t('如标准输出') }} </div>
    <div class="notice-content">
      <div class="notice-content-code echo">
        <div>disk_usage 0.75</div>
        <div>http_request_total{method="POST", route="/user"} 94334</div>
      </div>
    </div>
    <!-- <div class="notice-content">
            <div class="notice-content-desc"> {{ $t('CPU使用率') }} </div>
            <div class="notice-content-code">
                cpu_usage 0.75
            </div>
        </div>
        <div class="notice-title"> {{ $t('三、上报方法') }} </div>
        <div class="notice-content">
            <div class="notice-content-desc"> {{ $t('将需要上报的数据组装成以上格式的文本，然后对文本进行标准输出') }} </div>
            <div class="notice-content-desc">
                {{ $t('例如，编写shell脚本上报数据，可使用 `echo`') }}
            </div>
            <div class="notice-content-code">
                echo "disk_usage{disk_name=\"disk01\"} 0.75"
            </div>
        </div> -->
  </div>
</template>

<script>
export default {
  name: 'ShellSideNotice',
  methods: {
    handleGotoPage() {
      window.open(
        'https://github.com/prometheus/docs/blob/master/content/docs/instrumenting/exposition_formats.md',
        '_black'
      )
    }
  }
}
</script>

<style scoped lang="scss">
  .shell-side-notice {
    padding: 2px 10px 20px;
    background: #3b3c42;
    width: 333px;
    font-size: 12px;
    .notice-title {
      margin-top: 25px;
      height: 16px;
      font-size: 12px;
      font-weight: bold;
      color: rgba(255, 255, 255, 1);
      line-height: 16px;
    }
    .notice-content {
      &-desc {
        margin: 10px 0;
        height: 16px;
        font-size: 12px;
        color: rgba(196, 198, 204, 1);
        line-height: 16px;
        span {
          color: #3b73d1;
          &:hover {
            cursor: pointer;
          }
        }
      }
      &-code {
        width: 313px;
        background: #313238;
        padding: 10px;
        color: #ffb848;
        word-break: break-word;
        &.echo {
          padding: 10px 0;
        }
      }
    }
    .notice-table {
      margin: 10px 0;
      table {
        background: #313238;
        tr {
          height: 27px;
          border-bottom: .5px solid #3b3c42;
          td,
          th {
            padding-left: 10px;
            color: #c4c6cc;
            text-align: left;
          }
        }
      }
    }

  }
</style>
