import os
import gradio as gr
import json
from dotenv import load_dotenv

# 尝试导入cozepy，如果失败则使用模拟模式
try:
    from cozepy import Coze, TokenAuth, COZE_CN_BASE_URL

    COZEPY_AVAILABLE = True
except ImportError:
    COZEPY_AVAILABLE = False
    print("警告: cozepy 未安装，使用模拟模式")

# 加载环境变量
load_dotenv()


def get_coze_client():
    """获取Coze客户端"""
    if not COZEPY_AVAILABLE:
        return None

    coze_api_token = os.getenv("COZE_API_TOKEN")
    if not coze_api_token:
        print("警告: 未找到COZE_API_TOKEN环境变量，使用模拟模式")
        return None

    return Coze(auth=TokenAuth(token=coze_api_token), base_url=COZE_CN_BASE_URL)


def extract_markdown_text(response):
    """从Coze响应中提取Markdown格式文本"""
    try:
        # 如果响应是字符串，尝试解析为JSON
        if isinstance(response, str):
            response_data = json.loads(response)
        else:
            response_data = response

        # 提取data字段
        if hasattr(response_data, 'data'):
            data = response_data.data
        elif 'data' in response_data:
            data = response_data['data']
        else:
            return str(response_data)

        # 如果data是字符串，直接返回（保持Markdown格式）
        if isinstance(data, str):
            return data
        else:
            return str(data)

    except Exception as e:
        print(f"文本提取错误: {e}")
        return str(response)


def evaluate_with_coze(project_name, project_description, project_field, student_level, submission_materials):
    """使用Coze工作流进行评价"""
    coze = get_coze_client()
    workflow_id = os.getenv("WORKFLOW_ID")

    if not coze or not workflow_id:
        return evaluate_mock(project_name, project_description, project_field, student_level, submission_materials)

    try:
        # 准备工作流参数
        parameters = {
            "project_name": project_name,
            "project_description": project_description,
            "project_field": project_field,
            "student_level": student_level,
            "submission_materials": submission_materials
        }

        # 使用之前成功的方法调用
        response = coze.workflows.runs.stream(
            workflow_id=workflow_id,
            parameters=parameters
        )

        # 处理流式响应
        output_text = ""
        for event in response:
            # 打印事件类型以便调试
            print(f"事件类型: {type(event)}")
            print(f"事件内容: {event}")

            # 尝试提取消息内容
            if hasattr(event, 'message') and hasattr(event.message, 'content'):
                output_text += event.message.content + "\n"
            elif hasattr(event, 'content'):
                output_text += event.content + "\n"
            elif hasattr(event, 'output'):
                output_text += str(event.output) + "\n"

        # 提取Markdown格式文本
        markdown_text = extract_markdown_text(output_text if output_text else response)
        return markdown_text

    except Exception as e:
        return f"❌ Coze工作流错误：{str(e)}\n\n{evaluate_mock(project_name, project_description, project_field, student_level, submission_materials)}"


def evaluate_mock(project_name, project_description, project_field, student_level, submission_materials):
    """模拟评价函数 - 返回Markdown格式"""
    return f"""
# 🎓 项目评价报告 (模拟数据)

## 项目信息
- **项目名称**: {project_name}
- **项目领域**: {project_field}
- **学生水平**: {student_level}
- **提交材料**: {', '.join(submission_materials)}

## 项目描述
{project_description}

## 模拟评分结果
- **综合评分**: 8.2/10
- **创新性**: 7.5/10
- **技术难度**: 8.0/10
- **完成度**: 8.5/10
- **文档质量**: 7.0/10

## 项目优势
✅ 项目构思清晰，目标明确  
✅ 技术选型合理，符合当前技术趋势  
✅ 功能设计完整，用户体验考虑周到  

## 改进建议
📝 可以进一步优化项目文档结构  
📝 考虑添加更多创新功能点  
📝 建议完善测试用例  

## 学习收获
通过本项目，学生能够掌握**{project_field}**领域的基础知识和实践技能，提升问题解决能力和团队协作能力。

## 后续建议
1. 继续深入相关技术的学习
2. 参与更多实际项目积累经验
3. 关注行业最新发展趋势

---

*注：这是模拟评价，请配置Coze API Token和工作流ID后获取真实评价*
"""


def evaluate_project(project_name, project_description, project_field, student_level, submission_materials):
    """主评价函数"""
    return evaluate_with_coze(project_name, project_description, project_field, student_level, submission_materials)


def create_interface():
    """创建Gradio界面"""
    with gr.Blocks(theme=gr.themes.Soft(), title="学生项目智能评价系统") as demo:
        gr.Markdown("# 🎓 学生项目智能评价系统")

        # 显示当前模式
        if not COZEPY_AVAILABLE:
            gr.Markdown("⚠️ **当前模式: 模拟演示** (cozepy未安装)")
        elif not os.getenv("COZE_API_TOKEN"):
            gr.Markdown("⚠️ **当前模式: 模拟演示** (未配置COZE_API_TOKEN)")
        else:
            gr.Markdown("✅ **当前模式: Coze工作流**")

        with gr.Row():
            with gr.Column(scale=1):
                # 基础信息输入
                project_name = gr.Textbox(
                    label="项目名称",
                    placeholder="请输入项目名称...",
                    max_lines=1
                )

                student_level = gr.Dropdown(
                    choices=["初中", "高中", "本科", "研究生"],
                    label="学生水平",
                    value="本科"
                )

                project_field = gr.Dropdown(
                    choices=["技术开发", "艺术设计", "商业策划", "科学研究", "社会调查"],
                    label="项目领域",
                    value="技术开发"
                )

                submission_materials = gr.CheckboxGroup(
                    choices=["代码", "文档", "演示视频", "设计图", "数据报告"],
                    label="提交材料",
                    value=["代码", "文档"]
                )

            with gr.Column(scale=2):
                # 项目描述
                project_description = gr.Textbox(
                    label="项目描述",
                    placeholder="请详细描述您的项目内容、目标、技术实现、创新点等...",
                    lines=8,
                    max_lines=15
                )

        # 评估按钮
        evaluate_btn = gr.Button("开始评估", variant="primary", size="lg")

        # 结果显示区域 - 使用Markdown组件显示格式化的评价报告
        with gr.Column():
            gr.Markdown("## 📊 评估结果")
            output_markdown = gr.Markdown(
                label="评价报告",
                value="请点击\"开始评估\"按钮生成评价报告..."
            )

        # 配置说明
        with gr.Accordion("🔧 配置说明", open=False):
            gr.Markdown("""
            ### 如何启用Coze工作流模式：

            1. **安装cozepy**: `pip install cozepy>=0.19.0`
            2. **获取Coze API Token**: 
               - 登录 [Coze平台](https://www.coze.cn)
               - 点击右上角头像 → 个人中心 → 开发者配置 → 访问令牌
               - 创建并复制API Token
            3. **获取Workflow ID**:
               - 在Coze平台打开您的工作流
               - 从URL中复制工作流ID
            4. **创建.env文件**:
            ```
            COZE_API_TOKEN=您的API_Token
            WORKFLOW_ID=您的工作流ID
            ```
            """)

        # 示例数据
        with gr.Accordion("📝 查看示例", open=False):
            gr.Examples(
                examples=[
                    [
                        "智能校园导航系统",
                        "基于微信小程序的校园导航应用，集成教室查询、路径规划和活动通知功能。使用云开发技术实现，包含前端界面设计和后端数据处理。",
                        "技术开发",
                        "本科",
                        ["代码", "文档", "演示视频"]
                    ]
                ],
                inputs=[project_name, project_description, project_field, student_level, submission_materials]
            )

        # 绑定事件
        evaluate_btn.click(
            fn=evaluate_project,
            inputs=[project_name, project_description, project_field, student_level, submission_materials],
            outputs=output_markdown
        )

    return demo


if __name__ == "__main__":
    # 创建并启动界面
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7865,
        share=False  # 禁用分享功能，避免frpc错误
    )