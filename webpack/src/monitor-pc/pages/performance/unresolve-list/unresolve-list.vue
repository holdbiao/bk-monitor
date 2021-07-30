<script lang="ts">
import { Vue, Component, Prop } from 'vue-property-decorator'
// eslint-disable-next-line no-unused-vars
import { CreateElement } from 'vue'

@Component({ name: 'unresolve-list' })
export default class UnresolveList extends Vue {
  @Prop({ default: () => [], type: Array }) readonly list: any[]

  private statusMap = {
    1: window.i18n.t('致命'),
    2: window.i18n.t('预警'),
    3: window.i18n.t('提醒')
  }

  render(h: CreateElement) {
    return h(
      'ul',
      {
        class: 'unresolve-list'
      },
      this.list.map((item) => {
        const desc = `${this.statusMap[item.level]}(${item.count || 0})`
        const status = `item-${item.level}`
        return h(
          'li',
          {
            class: 'unresolve-list-item'
          },
          [
            h('span', {
              class: {
                'item-status': true,
                [status]: true
              }
            }),
            h('span', {
              class: 'item-name'
            }, desc)
          ]
        )
      })
    )
  }
}
</script>

<style scoped lang="scss">
  @import "../../home/common/mixins";

  $colors: $deadlyAlarmColor $warningAlarmColor $remindAlarmColor;

  .unresolve-list {
    padding: 0;
    margin: 0;
    &-item {
      display: flex;
      align-items: center;
      width: 120px;
      padding: 10px 6px 10px;
      color: #fff;

      @for $i from 1 through length($colors) {
        .item-#{$i} {
          background: nth($colors, $i);
        }
      }
      .item-status {
        flex: 0 0 14px;
        border-radius: 50%;
        height: 14px;
        margin-right: 8px;
      }
    }
  }
</style>
