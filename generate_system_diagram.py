import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

fig, ax = plt.subplots(1, 1, figsize=(28, 18))
ax.set_xlim(0, 28)
ax.set_ylim(0, 18)
ax.axis('off')
fig.patch.set_facecolor('#F8F9FA')

# ==================== HELPER FUNCTIONS ====================
def draw_box(ax, x, y, w, h, text, color='#2196F3', text_color='white', fontsize=9, bold=False, alpha=0.95, radius=0.15):
    box = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad={radius}",
                         facecolor=color, edgecolor='#444', linewidth=1.3, alpha=alpha)
    ax.add_patch(box)
    weight = 'bold' if bold else 'normal'
    ax.text(x + w/2, y + h/2, text, ha='center', va='center',
            fontsize=fontsize, color=text_color, fontweight=weight,
            fontfamily='sans-serif', linespacing=1.4)

def draw_arrow(ax, x1, y1, x2, y2, color='#666', lw=1.8, style='->', text='', text_pos='mid'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                               connectionstyle="arc3,rad=0.05"))
    if text:
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        offset_x = 0.3 if text_pos == 'mid' else 0
        offset_y = 0.25 if text_pos == 'mid' else 0
        ax.text(mx + offset_x, my + offset_y, text, ha='center', va='center',
                fontsize=7.5, color=color, fontfamily='sans-serif',
                fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=color, alpha=0.9))

def draw_section_box(ax, x, y, w, h, title, color, title_color):
    section = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2",
                             facecolor='white', edgecolor=color, linewidth=2.5, alpha=0.5)
    ax.add_patch(section)
    ax.text(x + w/2, y + h - 0.35, title, ha='center', va='center',
            fontsize=13, color=title_color, fontweight='bold', fontfamily='sans-serif')
    # colored top bar
    bar = FancyBboxPatch((x, y + h - 0.6), w, 0.6, boxstyle="round,pad=0.05",
                         facecolor=color, edgecolor='none', alpha=0.85)
    ax.add_patch(bar)
    ax.text(x + w/2, y + h - 0.3, title, ha='center', va='center',
            fontsize=12, color='white', fontweight='bold', fontfamily='sans-serif')

# ==================== TITLE ====================
ax.text(14, 17.5, 'SO DO HE THONG - QUY TRINH DEPLOY TU SOURCE CODE DEN INTERNET',
        ha='center', va='center', fontsize=20, fontweight='bold',
        color='#1565C0', fontfamily='sans-serif')
ax.text(14, 17.1, 'Management Rent Room  |  quock6.click',
        ha='center', va='center', fontsize=11, color='#888', fontfamily='sans-serif')

# ==================== SECTION 1: MAY DEVELOPER (Left) ====================
draw_section_box(ax, 0.3, 8.5, 6.5, 8.2, 'MAY DEVELOPER (Local)', '#1565C0', '#1565C0')

draw_box(ax, 0.8, 14.8, 5.5, 1.2, '1. VIET CODE\nBackend (Java/Spring Boot)\nFrontend (React/JS)', '#BBDEFB', '#1565C0', 9, True)
draw_box(ax, 0.8, 13.2, 5.5, 1.2, '2. TEST LOCAL\ndocker-compose up\nhttp://localhost:3100', '#C8E6C9', '#2E7D32', 9, True)
draw_box(ax, 0.8, 11.6, 5.5, 1.2, '3. TAO SSH KEY\nssh-keygen -t rsa -b 4096\nLuu private key', '#E1BEE7', '#6A1B9A', 9, True)
draw_box(ax, 0.8, 10.0, 5.5, 1.2, '4. PUSH CODE\ngit add . && git commit\ngit push origin main', '#FFE0B2', '#E65100', 9, True)
draw_box(ax, 0.8, 8.8, 5.5, 0.9, '5. DATA\nPrivate Key (id_rsa)\nSource code (.git)', '#F3E5F5', '#7B1FA2', 8, False)

# Arrows local
draw_arrow(ax, 3.55, 14.8, 3.55, 14.4, '#1565C0', 1.5)
draw_arrow(ax, 3.55, 13.2, 3.55, 12.8, '#2E7D32', 1.5)
draw_arrow(ax, 3.55, 11.6, 3.55, 11.2, '#6A1B9A', 1.5)
draw_arrow(ax, 3.55, 10.0, 3.55, 9.7, '#E65100', 1.5)

# ==================== SECTION 2: GITHUB (Center-Top) ====================
draw_section_box(ax, 8.0, 11.0, 8.0, 5.7, 'GITHUB.COM', '#333', '#333')

draw_box(ax, 8.5, 14.8, 7.0, 1.0, 'REPOSITORY: quoc05dev/Managerment-rent-room', '#424242', 'white', 9, True)
draw_box(ax, 8.5, 13.5, 3.2, 1.0, 'SOURCE CODE\n.git', '#616161', 'white', 8, False)
draw_box(ax, 12.3, 13.5, 3.2, 1.0, 'SECRETS\nSERVER_HOST\nSERVER_USER\nSERVER_SSH_KEY', '#B71C1C', 'white', 8, False)

# CI/CD Pipeline
draw_box(ax, 8.5, 12.0, 7.0, 1.2, 'GITHUB ACTIONS CI/CD\nDong bo voi moi push len main', '#1B5E20', 'white', 10, True)

draw_box(ax, 8.5, 11.2, 2.1, 0.6, 'Build\nDocker', '#4CAF50', 'white', 8, True)
draw_box(ax, 10.8, 11.2, 2.1, 0.6, 'Test\nLint+Compile', '#4CAF50', 'white', 8, True)
draw_box(ax, 13.1, 11.2, 2.4, 0.6, 'Deploy\nSSH -> Server', '#4CAF50', 'white', 8, True)

draw_arrow(ax, 9.55, 12.0, 9.55, 11.8, 'white', 1.2)
draw_arrow(ax, 11.85, 12.0, 11.85, 11.8, 'white', 1.2)
draw_arrow(ax, 14.3, 12.0, 14.3, 11.8, 'white', 1.2)

# Arrow from local to GitHub
draw_arrow(ax, 6.3, 10.6, 8.0, 10.6, '#E65100', 2, text='git push', text_pos='mid')

# ==================== SECTION 3: SERVER VPS (Right) ====================
draw_section_box(ax, 17.3, 1.5, 10.4, 15.2, 'SERVER VPS (quock6.click)', '#D32F2F', '#D32F2F')

# Server steps
draw_box(ax, 17.8, 14.8, 9.4, 1.2, 'STEP 1: NHAN CODE\ngit pull origin main\nLay code moi nhat tu GitHub', '#FFCDD2', '#C62828', 9, True)

draw_box(ax, 17.8, 13.2, 9.4, 1.2, 'STEP 2: DOCKER BUILD\ndocker compose up -d --build\nBuild image Backend + Frontend', '#FFCCBC', '#BF360C', 9, True)

draw_box(ax, 17.8, 11.6, 9.4, 1.2, 'STEP 3: CHAY CONTAINERS\n4 containers tu dong khoi dong:\nMySQL | ActiveMQ | Backend | Frontend', '#FFF9C4', '#F57F17', 9, True)

draw_box(ax, 17.8, 10.0, 9.4, 1.2, 'STEP 4: NGINX HOST\nQuock6.click:80 -> Frontend:3100\nQuock6.click:80 -> Backend:8081', '#DCEDC8', '#33691E', 9, True)

# Container details
draw_box(ax, 17.8, 7.8, 4.5, 1.8, 'CONTAINERS:\n- rental-mysql (:3306)\n- rental-activemq (:61616)\n- rental-backend (:8080)\n- rental-frontend (:80)', '#E3F2FD', '#1565C0', 8, False)

draw_box(ax, 12.5, 7.8, 4.5, 1.8, 'VOLUMES (persist data):\n- mysql-data\n- activemq-data\n- activemq-log\n- upload-data', '#FCE4EC', '#C62828', 8, False)

draw_box(ax, 17.8, 5.8, 9.4, 1.5, 'DAU RA:\nFrontend: http://localhost:3100 -> http://quock6.click\nBackend API: http://localhost:8081 -> http://quock6.click/*', '#E8F5E9', '#1B5E20', 9, False)

# ==================== SECTION 4: INTERNET (Far Right) ====================
draw_section_box(ax, 17.3, 1.5, 10.4, 4.0, 'INTERNET (Nguoi dung)', '#FF6F00', '#FF6F00')

draw_box(ax, 17.8, 3.5, 4.0, 1.2, 'USER\nMo trinh duyet\ngo quock6.click', '#FFF3E0', '#E65100', 9, False)
draw_box(ax, 22.2, 3.5, 5.0, 1.2, 'GOOGLE DNS\nquock6.click\n-> IP Server VPS', '#FFE0B2', '#BF360C', 9, False)
draw_box(ax, 17.8, 2.0, 9.4, 1.2, 'TRA NHAN:\nTrang web + API + Hinh anh\nWebSocket (chat real-time)', '#FBE9E7', '#BF360C', 9, False)

# ==================== CONNECTING ARROWS ====================
# GitHub -> Server (SSH Deploy)
draw_arrow(ax, 15.5, 11.5, 17.3, 15.0, '#D32F2F', 2.5, text='SSH Deploy\n(server script)', text_pos='mid')

# Server internal flow
draw_arrow(ax, 22.5, 14.8, 22.5, 14.4, '#C62828', 1.5)
draw_arrow(ax, 22.5, 13.2, 22.5, 12.8, '#BF360C', 1.5)
draw_arrow(ax, 22.5, 11.6, 22.5, 11.2, '#F57F17', 1.5)
draw_arrow(ax, 22.5, 10.0, 22.5, 9.6, '#33691E', 1.5)

# Server -> Internet
draw_arrow(ax, 22.5, 7.5, 22.5, 5.5, '#1B5E20', 2)
draw_arrow(ax, 19.8, 4.1, 17.3, 3.9, '#E65100', 2)
draw_arrow(ax, 22.5, 3.5, 22.5, 3.2, '#BF360C', 1.5)

# ==================== LEGEND ====================
legend_y = 0.3
legend_items = [
    ('#1565C0', 'Developer Machine'),
    ('#333333', 'GitHub Repository'),
    ('#1B5E20', 'CI/CD Pipeline'),
    ('#D32F2F', 'Server VPS'),
    ('#FF6F00', 'Internet / Users'),
]
for i, (color, label) in enumerate(legend_items):
    x = 3 + i * 5
    box = FancyBboxPatch((x, legend_y), 0.4, 0.4, boxstyle="round,pad=0.05",
                         facecolor=color, edgecolor='none', alpha=0.85)
    ax.add_patch(box)
    ax.text(x + 0.6, legend_y + 0.2, label, ha='left', va='center',
            fontsize=9, color='#333', fontfamily='sans-serif')

# Flow description
flow_text = 'QUY TRINH: Developer viet code -> git push -> GitHub Actions build & test -> SSH deploy -> Server build docker -> Nginx phuc vu Internet'
ax.text(14, 0.9, flow_text, ha='center', va='center', fontsize=9, color='#555',
        fontfamily='sans-serif', style='italic',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#E3F2FD', edgecolor='#1565C0', alpha=0.8))

plt.tight_layout(pad=0.3)
output = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'SoDoHeThong_Deploy.png')
plt.savefig(output, dpi=200, bbox_inches='tight', facecolor='#F8F9FA')
plt.close()
print(f'Da tao so do he thong tai: {output}')
