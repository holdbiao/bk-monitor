<template>
    <div ref="viewer"></div>
</template>
<script lang="ts">
    import Editor from './toastui-editor-viewer'
    import './toastui-editor.css'
    import { Vue, Prop, Component, Watch } from 'vue-property-decorator'
    @Component({
        name: 'markdown-editor'
    })
    export default class MarkdowViewer extends Vue {
        editor: any = null
        editorEvents: string[] = ['load', 'change', 'stateChange', 'focus', 'blur']
        @Prop()
        height: string
        @Prop()
        value: string
        @Prop()
        exts: []

        @Watch('value')
        onValueChange (val, preVal) {
            if (val !== preVal) {
                this.editor.setMarkdown(val)
            }
        }

        mounted () {
            const eventOption = {}
            this.editorEvents.forEach(event => {
                eventOption[event] = (...args) => {
                    this.$emit(event, ...args)
                }
            })

            this.editor = new Editor({
                el: this.$refs.viewer,
                exts: this.exts,
                events: eventOption,
                initialValue: this.value,
                height: this.height,
                viewer: true
            })
        }

        destroyed () {
            this.editorEvents.forEach(event => {
                this.editor.off(event)
            })
            this.editor.remove()
        }

        invoke (methodName, ...args) {
            let result = null
            if (this.editor[methodName]) {
                result = this.editor[methodName](...args)
            }
            return result
        }
    }
</script>
