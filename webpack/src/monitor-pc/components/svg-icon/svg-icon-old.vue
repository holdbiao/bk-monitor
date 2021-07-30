<template>
    <span :class="className" :style="{ 'width': `${size}px`,height: `${size}px` }"></span>
</template>

<script>
    export default {
        name: 'svg-icon',
        props: {
            iconClass: {
                type: String,
                required: true
            },
            size: {
                type: Number,
                default: 16
            }
        },
        computed: {
            className () {
                return `svg-icon-${this.iconClass}`
            }
        }
    }
</script>

<style scoped lang="scss">
    @import "../../pc/pages/home/common/mixins";

    .common-icon {
        background-size: cover;
        width: 10px;
        height: 10px;
        display: inline-block;
    }

    @for $i from 1 through length($icons) {
        .svg-icon-#{nth($icons,$i)} {
            @extend .common-icon;
            background-image: url("../../static/images/icons/#{nth($icons,$i)}.svg");
        }
    }
</style>
