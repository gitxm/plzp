#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单模式处理器 - 基于菜单的用户界面
提供清晰的菜单选择，支持单文件处理、批量处理和基本配置
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.processors.enhanced_data_processor import EnhancedDataProcessor


class SimpleProcessor:
    """简单模式处理器"""

    def __init__(self):
        self.processor = EnhancedDataProcessor()
        from app.config import MULTITHREADING_CONFIG
        self.user_settings_path = Path('config/user_settings.json')
        # 默认设置
        self.settings = {
            'output_folder': './output',
            'recursive': False,
            'account_filter': None,
            'multithreading_enabled': MULTITHREADING_CONFIG['enable_multithreading'],
            'max_threads': MULTITHREADING_CONFIG['max_download_threads'],
            'download_timeout': MULTITHREADING_CONFIG['download_timeout']
        }
        # 尝试加载用户配置并应用
        self.load_user_settings()
        self.apply_settings_to_processor()

    # ===== 持久化配置功能 =====
    def load_user_settings(self):
        """从本地配置文件加载用户设置，覆盖默认设置"""
        try:
            import json
            cfg_path = self.user_settings_path
            if cfg_path.exists():
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    # 只覆盖已知键，避免脏数据
                    for k in list(self.settings.keys()):
                        if k in data:
                            self.settings[k] = data[k]
                print(f"✅ 已加载用户配置: {cfg_path}")
        except Exception as e:
            print(f"❌ 加载用户配置失败: {e}")

    def save_user_settings(self):
        """将当前设置保存到本地配置文件"""
        try:
            import json
            cfg_path = self.user_settings_path
            cfg_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cfg_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            print(f"💾 配置已保存: {cfg_path}")
        except Exception as e:
            print(f"❌ 保存用户配置失败: {e}")

    def reset_user_settings(self):
        """重置为默认配置并删除用户配置文件"""
        try:
            from app.config import MULTITHREADING_CONFIG
            # 恢复默认
            self.settings = {
                'output_folder': './output',
                'recursive': False,
                'account_filter': None,
                'multithreading_enabled': MULTITHREADING_CONFIG['enable_multithreading'],
                'max_threads': MULTITHREADING_CONFIG['max_download_threads'],
                'download_timeout': MULTITHREADING_CONFIG['download_timeout']
            }
            # 删除文件
            if self.user_settings_path.exists():
                self.user_settings_path.unlink()
            # 应用到处理器
            self.apply_settings_to_processor()
            print("✅ 已重置为默认配置")
        except Exception as e:
            print(f"❌ 重置配置失败: {e}")

    def apply_settings_to_processor(self):
        """将当前设置应用到处理器实例"""
        try:
            self.processor.set_multithreading_enabled(self.settings['multithreading_enabled'])
            self.processor.set_max_threads(self.settings['max_threads'])
            self.processor.set_download_timeout(self.settings['download_timeout'])
        except Exception as e:
            print(f"❌ 应用配置到处理器失败: {e}")

    def clean_account_id(self, account_id):
        """清理账户ID格式，支持各种输入格式"""
        if not account_id:
            return ""

        # 转换为字符串并去除首尾空格
        account_id = str(account_id).strip()

        # 去除各种引号
        account_id = account_id.strip("'\"")

        # 去除空格
        account_id = account_id.strip()

        return account_id

    def parse_account_ids(self, ids_input):
        """解析账户ID列表，支持多种格式"""
        if not ids_input:
            return []

        import re
        # 使用正则表达式分割，支持逗号、中文逗号、空格等分隔符
        parts = re.split(r'[，,\s]+', ids_input)

        # 清理每个账户ID
        cleaned_ids = []
        for part in parts:
            cleaned_id = self.clean_account_id(part)
            if cleaned_id:
                cleaned_ids.append(cleaned_id)

        return cleaned_ids

    def extract_main_domain(self, full_domain):
        """提取主域名，去除子域名前缀"""
        if not full_domain:
            return None

        # 分割域名
        parts = full_domain.split('.')

        # 如果域名部分少于2个，直接返回
        if len(parts) < 2:
            return full_domain

        # 常见的顶级域名列表（可以根据需要扩展）
        common_tlds = {
            'com', 'org', 'net', 'edu', 'gov', 'mil', 'int',
            'co.uk', 'com.cn', 'com.au', 'co.jp', 'com.br'
        }

        # 检查是否是复合顶级域名（如 co.uk, com.cn）
        if len(parts) >= 3:
            potential_tld = '.'.join(parts[-2:])
            if potential_tld in common_tlds:
                # 返回最后三级域名（如 example.co.uk）
                return '.'.join(parts[-3:]) if len(parts) >= 3 else full_domain

        # 默认返回最后两级域名（如 example.com）
        return '.'.join(parts[-2:])

    def compute_domain_stats(self, df):
        """
        基于给定数据框，计算主域名分布（仅使用 url 字段；若无则返回空字典）
        """
        domain_stats = {}
        if 'url' not in df.columns:
            return domain_stats
        from urllib.parse import urlparse
        for url in df['url'].dropna():
            try:
                full_domain = urlparse(str(url)).netloc
                if full_domain:
                    main_domain = self.extract_main_domain(full_domain)
                    if main_domain:
                        domain_stats[main_domain] = domain_stats.get(main_domain, 0) + 1
            except:
                continue
        return domain_stats

    def analyze_data_file(self, file_path):
        """分析数据文件，提取统计信息"""
        try:
            # 加载数据
            df = self.processor.load_data_file(file_path)
            if df is None or df.empty:
                return None

            # 基本统计
            total_rows = len(df)

            # 仅使用 url 字段进行URL统计
            if 'url' in df.columns:
                valid_urls = df['url'].notna().sum()
            else:
                valid_urls = 0

            # 账户ID统计
            account_stats = df['account_id'].value_counts().to_dict()

            # 用户ID统计（按账户分组）
            user_stats = {}
            for account_id in account_stats.keys():
                account_df = df[df['account_id'] == account_id]
                user_stats[account_id] = account_df['user_id'].value_counts().to_dict()

            # URL域名统计（仅基于 url 字段）
            domain_stats = self.compute_domain_stats(df)

            return {
                'total_rows': total_rows,
                'valid_urls': valid_urls,
                'account_stats': account_stats,
                'user_stats': user_stats,
                'domain_stats': domain_stats,
                'dataframe': df
            }

        except Exception as e:
            print(f"❌ 数据分析失败: {e}")
            return None

    def show_data_preview(self, analysis):
        """显示数据预览"""
        print("\n📊 数据文件分析结果")
        print("=" * 50)
        print(f"📄 总行数: {analysis['total_rows']}")
        print(f"🔗 有效URL数量: {analysis['valid_urls']}")
        print(f"👥 不同账户数量: {len(analysis['account_stats'])}")

        # 域名信息显示
        if analysis['domain_stats']:
            print(f"🌐 不同域名数量: {len(analysis['domain_stats'])}")
        else:
            print("🌐 域名信息: 无域名信息可用（缺少url字段）")

    def interactive_data_filter(self, analysis):
        """交互式数据筛选"""
        print("\n🔍 智能数据筛选")
        print("=" * 50)

        # 第一级：账户筛选
        selected_accounts = self.select_accounts(analysis['account_stats'])
        if not selected_accounts:
            return None

        # 第二级：用户筛选
        selected_users = self.select_users(analysis['user_stats'], selected_accounts)
        if not selected_users:
            return None

        # 第三级：域名筛选（基于已选账户/用户的子集重新计算域名）
        selected_domains = None
        # 先根据前两级筛选出子集
        subset_df = analysis['dataframe']
        if selected_accounts:
            subset_df = subset_df[subset_df['account_id'].isin(selected_accounts)]
        if selected_users:
            subset_df = subset_df[subset_df['user_id'].isin(selected_users)]
        # 基于子集计算域名分布
        subset_domain_stats = self.compute_domain_stats(subset_df)

        if subset_domain_stats:
            selected_domains = self.select_domains(subset_domain_stats)
            if selected_domains is False:  # 用户取消
                return None
        else:
            print("\n🔸 第三级筛选：域名筛选")
            print("-" * 30)
            print("⚠️ 当前已选账户/用户下无可用域名，跳过域名筛选")
            selected_domains = None

        # 应用筛选条件
        filtered_df = self.apply_filters(
            analysis['dataframe'],
            selected_accounts,
            selected_users,
            selected_domains
        )

        return {
            'dataframe': filtered_df,
            'accounts': selected_accounts,
            'users': selected_users,
            'domains': selected_domains
        }

    def select_accounts(self, account_stats):
        """第一级筛选：选择账户ID"""
        print("\n🔸 第一级筛选：账户ID选择")
        print("-" * 30)

        accounts = list(account_stats.keys())
        print(f"共有 {len(accounts)} 个账户:")

        for i, (account_id, count) in enumerate(account_stats.items(), 1):
            print(f"  {i}. 账户 {account_id} ({count} 条数据)")

        print(f"\n选择选项:")
        print("  a. 全选所有账户")
        print("  s. 手动选择账户（输入序号，用逗号分隔）")
        print("  c. 取消筛选")

        while True:
            choice = input("\n请选择 (a/s/c): ").strip().lower()

            if choice == 'a':
                return accounts
            elif choice == 's':
                selected_indices = input("请输入账户序号（如: 1,3,5）: ").strip()
                try:
                    indices = [int(x.strip()) - 1 for x in selected_indices.split(',')]
                    selected = [accounts[i] for i in indices if 0 <= i < len(accounts)]
                    if selected:
                        print(f"✅ 已选择 {len(selected)} 个账户: {', '.join(map(str, selected))}")
                        return selected
                    else:
                        print("❌ 无效的选择")
                        return None
                except:
                    print("❌ 输入格式错误")
                    return None
            elif choice == 'c':
                return None
            else:
                print("❌ 无效选项，请输入 a（全选）、s（手动选择）或 c（取消筛选）")
                continue

    def select_users(self, user_stats, selected_accounts):
        """第二级筛选：选择用户ID"""
        print("\n🔸 第二级筛选：用户ID选择")
        print("-" * 30)

        # 收集所选账户的所有用户
        all_users = {}
        for account_id in selected_accounts:
            if account_id in user_stats:
                for user_id, count in user_stats[account_id].items():
                    if user_id in all_users:
                        all_users[user_id] += count
                    else:
                        all_users[user_id] = count

        users = list(all_users.keys())
        print(f"所选账户中共有 {len(users)} 个用户:")

        for i, (user_id, count) in enumerate(all_users.items(), 1):
            print(f"  {i}. 用户 {user_id} ({count} 条数据)")

        print(f"\n选择选项:")
        print("  a. 全选所有用户")
        print("  s. 手动选择用户（输入序号，用逗号分隔）")
        print("  c. 取消筛选")

        while True:
            choice = input("\n请选择 (a/s/c): ").strip().lower()

            if choice == 'a':
                return users
            elif choice == 's':
                selected_indices = input("请输入用户序号（如: 1,3,5）: ").strip()
                try:
                    indices = [int(x.strip()) - 1 for x in selected_indices.split(',')]
                    selected = [users[i] for i in indices if 0 <= i < len(users)]
                    if selected:
                        print(f"✅ 已选择 {len(selected)} 个用户: {', '.join(map(str, selected))}")
                        return selected
                    else:
                        print("❌ 无效的选择")
                        return None
                except:
                    print("❌ 输入格式错误")
                    return None
            elif choice == 'c':
                return None
            else:
                print("❌ 无效选项，请输入 a（全选）、s（手动选择）或 c（取消筛选）")
                continue

    def select_domains(self, domain_stats):
        """第三级筛选：选择URL域名"""
        if not domain_stats:
            return False

        print("\n🔸 第三级筛选：URL域名选择")
        print("-" * 30)

        domains = list(domain_stats.keys())
        print(f"共有 {len(domains)} 个域名:")

        for i, (domain, count) in enumerate(domain_stats.items(), 1):
            print(f"  {i}. {domain} ({count} 张图片)")

        print(f"\n选择选项:")
        print("  a. 全选所有域名")
        print("  s. 手动选择域名（输入序号，用逗号分隔）")
        print("  k. 关键词匹配（输入域名关键词）")
        print("  c. 取消筛选")

        while True:
            choice = input("\n请选择 (a/s/k/c): ").strip().lower()

            if choice == 'a':
                return domains
            elif choice == 's':
                selected_indices = input("请输入域名序号（如: 1,3,5）: ").strip()
                try:
                    indices = [int(x.strip()) - 1 for x in selected_indices.split(',')]
                    selected = [domains[i] for i in indices if 0 <= i < len(domains)]
                    if selected:
                        print(f"✅ 已选择 {len(selected)} 个域名: {', '.join(selected)}")
                        return selected
                    else:
                        print("❌ 无效的选择")
                        return False
                except:
                    print("❌ 输入格式错误")
                    return False
            elif choice == 'k':
                # 关键词匹配（不区分大小写，支持多个关键词逗号分隔；支持排除关键词，前缀为 '-'）
                while True:
                    kw_input = input("请输入域名关键词（如: amazon 或 amazon,temu，支持排除：如-cdn,支持用逗号分割多选）: ").strip()
                    if not kw_input:
                        print("❌ 关键词不能为空")
                        retry = input("是否重新输入？(y/n): ").strip().lower()
                        if retry != 'y':
                            return False
                        continue
                    tokens = [k.strip().lower() for k in kw_input.split(',') if k.strip()]
                    positives = [t for t in tokens if not t.startswith('-')]
                    negatives = [t[1:] for t in tokens if t.startswith('-') and len(t) > 1]

                    # 基础候选集：若无正向关键词，则从所有域名开始，否则从命中任一正向关键词的域名开始
                    base = []
                    if positives:
                        for d in domains:
                            dl = d.lower()
                            if any(p in dl for p in positives):
                                base.append(d)
                    else:
                        base = list(domains)

                    # 应用排除关键词过滤
                    matched = []
                    seen = set()
                    for d in base:
                        dl = d.lower()
                        if any(n in dl for n in negatives):
                            continue
                        if d not in seen:
                            matched.append(d)
                            seen.add(d)

                    if not matched:
                        print("❌ 未匹配到任何域名")
                        retry = input("是否重新输入关键词？(y/n): ").strip().lower()
                        if retry == 'y':
                            continue
                        return False
                    print("✅ 找到匹配域名:")
                    for d in matched:
                        print(f"  - {d} ({domain_stats.get(d, 0)} 张图片)")
                    confirm = input("确认选择这些域名吗？(y/n): ").strip().lower()
                    if confirm == 'y':
                        print(f"✅ 已选择 {len(matched)} 个域名: {', '.join(matched)}")
                        return matched
                    retry = input("是否重新输入关键词？(y/n): ").strip().lower()
                    if retry != 'y':
                        return False
            elif choice == 'c':
                return False
            else:
                print("❌ 无效选项，请输入 a（全选）、s（手动选择）、k（关键词匹配）或 c（取消筛选）")
                continue

    def apply_filters(self, df, selected_accounts, selected_users, selected_domains):
        """应用筛选条件"""
        filtered_df = df.copy()

        # 应用账户筛选
        if selected_accounts:
            filtered_df = filtered_df[filtered_df['account_id'].isin(selected_accounts)]

        # 应用用户筛选
        if selected_users:
            filtered_df = filtered_df[filtered_df['user_id'].isin(selected_users)]

        # 应用域名筛选（仅在有域名数据且有url字段时）
        if selected_domains and 'url' in filtered_df.columns:
            from urllib.parse import urlparse

            def url_in_domains(url):
                try:
                    full_domain = urlparse(str(url)).netloc
                    # 提取主域名进行比较
                    main_domain = self.extract_main_domain(full_domain)
                    return main_domain in selected_domains
                except:
                    return False

            filtered_df = filtered_df[filtered_df['url'].apply(url_in_domains)]

        return filtered_df

    def process_filtered_data(self, filtered_df, original_file_path, output_folder):
        """处理智能筛选后的数据"""
        try:
            from pathlib import Path

            # 准备输出路径
            input_path = Path(original_file_path)
            if output_folder:
                output_folder_path = Path(output_folder)
            else:
                # 默认使用配置文件中指定的输出文件夹
                from app.config import DEFAULT_OUTPUT_FOLDER
                output_folder_path = Path(DEFAULT_OUTPUT_FOLDER)

            # 创建输出文件夹
            output_folder_path.mkdir(parents=True, exist_ok=True)

            # 设置输出文件路径和基础文件夹
            output_file_path = output_folder_path / f"{input_path.stem}_filtered.xlsx"
            base_folder = output_folder_path / f"{input_path.stem}_filtered"

            # 创建基础文件夹
            base_folder.mkdir(parents=True, exist_ok=True)

            # 下载图片
            success_count = self.processor.download_images_for_dataframe(filtered_df, base_folder)

            # 保存筛选后的文件
            filtered_df.to_excel(output_file_path, index=False)

            # 显示完成信息（使用绝对路径）
            output_abs_path = output_folder_path.resolve()
            output_file_abs_path = output_file_path.resolve()
            base_folder_abs_path = base_folder.resolve()

            print("\n" + "=" * 60)
            print("✅ 智能筛选处理完成！")
            print("=" * 60)
            print(f"📁 输出目录: {output_abs_path}")
            print(f"📄 数据文件: {output_file_abs_path}")
            print(f"🖼️  图片目录: {base_folder_abs_path}")
            print(f"📊 成功下载: {success_count}/{len(filtered_df)} 张图片")

            # 显示错误日志摘要
            error_summary = self.processor.get_error_log_summary()
            if error_summary['error_count'] > 0:
                print(f"❌ 下载错误: {error_summary['error_count']} 个")
                print(f"📋 错误日志: {error_summary['error_log_file']}")
            else:
                print("✅ 所有图片下载成功，无错误记录")
            print("=" * 60)

            return True

        except Exception as e:
            print(f"❌ 智能筛选处理失败: {e}")
            return False

    def show_filter_summary(self, filtered_data, original_count):
        """显示筛选结果摘要"""
        print("\n" + "=" * 60)
        print("🎯 筛选结果摘要")
        print("=" * 60)
        print(f"📊 原始数据量: {original_count} 条")
        print(f"📊 筛选后数据量: {len(filtered_data['dataframe'])} 条")
        print(f"📈 筛选比例: {len(filtered_data['dataframe'])/original_count*100:.1f}%")
        print()
        print(f"👥 选中账户 ({len(filtered_data['accounts'])} 个):")
        for account in filtered_data['accounts']:
            account_count = len(filtered_data['dataframe'][filtered_data['dataframe']['account_id'] == account])
            print(f"   - 账户 {account}: {account_count} 条数据")
        print()
        print(f"🆔 选中用户 ({len(filtered_data['users'])} 个):")
        for user in filtered_data['users']:
            user_count = len(filtered_data['dataframe'][filtered_data['dataframe']['user_id'] == user])
            print(f"   - 用户 {user}: {user_count} 条数据")
        print()
        # 域名筛选摘要（仅在有域名数据时显示）
        if filtered_data['domains'] and 'url' in filtered_data['dataframe'].columns:
            print(f"🌐 选中域名 ({len(filtered_data['domains'])} 个):")
            from urllib.parse import urlparse

            for domain in filtered_data['domains']:
                domain_count = 0
                for url in filtered_data['dataframe']['url']:
                    try:
                        full_domain = urlparse(str(url)).netloc
                        main_domain = self.extract_main_domain(full_domain)
                        if main_domain == domain:
                            domain_count += 1
                    except:
                        continue
                print(f"   - {domain}: {domain_count} 张图片")
        else:
            print("🌐 域名筛选: 跳过（无url字段）")
        print("=" * 60)

    def print_welcome(self):
        """打印欢迎信息"""
        print("=" * 60)
        print("📊 数据处理和图片下载工具 - 简单模式")
        print("=" * 60)
        print("功能: 从Excel/CSV提取数据，下载图片，整理文件")
        print("特性: 时间格式优化、重复文件检查、账户筛选")
        print("=" * 60)

    def print_main_menu(self):
        """打印主菜单"""
        print("\n🚀 请选择操作:")
        print("  1. 处理单个文件")
        print("  2. 批量处理文件夹")
        print("  3. 查看文件夹内容")
        print("  4. 检测文件格式")
        print("  5. 设置配置")
        print("  6. 查看当前设置")
        print("  7. 返回主程序")
        print("-" * 40)

    def get_user_choice(self, max_choice=7):
        """获取用户选择"""
        while True:
            try:
                choice = input(f"请输入选择 (1-{max_choice}): ").strip()
                if choice.isdigit() and 1 <= int(choice) <= max_choice:
                    return int(choice)
                else:
                    print(f"❌ 请输入有效选择 (1-{max_choice})")
            except KeyboardInterrupt:
                print("\n\n👋 程序已退出")
                return -1
            except:
                print("❌ 输入无效，请重新输入")

    def handle_single_file(self):
        """处理单个文件"""
        print("\n📄 单文件处理")
        print("-" * 30)

        # 获取文件路径
        print("💡 提示: 可以直接拖拽文件到终端，或输入完整路径")
        file_path = input("请输入文件路径 (支持 .xlsx, .xls, .csv): ").strip()

        if not file_path:
            print("❌ 文件路径不能为空")
            return

        # 处理路径中的引号
        file_path = file_path.strip("'\"")

        # 展开用户目录路径
        file_path = os.path.expanduser(file_path)

        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            print(f"🔍 检查路径: {os.path.abspath(file_path)}")
            print("💡 请确保:")
            print("   1. 路径正确无误")
            print("   2. 文件确实存在")
            print("   3. 有读取权限")
            return

        # 数据预览和智能筛选
        print("\n🔍 正在分析数据文件...")
        analysis = self.analyze_data_file(file_path)
        if not analysis:
            print("❌ 数据文件分析失败")
            return

        # 显示数据预览
        self.show_data_preview(analysis)

        # 询问是否进行智能筛选
        print("\n" + "=" * 50)
        print("🎯 数据筛选选项:")
        print("  1. 使用智能筛选（推荐）- 多级筛选账户、用户、域名")
        print("  2. 使用简单筛选 - 仅筛选账户ID")
        print("  3. 全量处理 - 处理所有数据")

        filter_choice = self.get_user_choice(3)
        if filter_choice == -1:
            return

        filtered_data = None
        account_filter = None

        if filter_choice == 1:
            # 智能筛选
            filtered_data = self.interactive_data_filter(analysis)
            if not filtered_data:
                print("❌ 筛选已取消")
                return

            # 显示详细的筛选结果摘要
            self.show_filter_summary(filtered_data, analysis['total_rows'])

        elif filter_choice == 2:
            # 简单账户筛选
            account_filter = self.settings['account_filter']
            if account_filter is None:
                account_filter = self.interactive_account_filter_setup()
                if account_filter is False:
                    return

        # 如果没有使用智能筛选，account_filter 现在包含筛选列表或 None（全量处理）

        print(f"\n🔄 开始处理文件: {file_path}")
        print(f"📁 输出文件夹: {self.settings['output_folder']}")

        # 显示筛选信息
        if filtered_data:
            print(f"🎯 使用智能筛选: {len(filtered_data['dataframe'])} 条数据")
            print(f"  👥 账户: {', '.join(map(str, filtered_data['accounts']))}")
            print(f"  🆔 用户: {', '.join(map(str, filtered_data['users']))}")
            print(f"  🌐 域名: {', '.join(filtered_data['domains'])}")
        elif account_filter:
            print(f"🔍 账户筛选: {', '.join(account_filter)}")
        else:
            print("🔍 处理模式: 全量处理（所有账户）")

        # 应用多线程设置（使用配置或用户设置）
        self.processor.set_multithreading_enabled(self.settings['multithreading_enabled'])
        self.processor.set_max_threads(self.settings['max_threads'])
        self.processor.set_download_timeout(self.settings['download_timeout'])

        # 以处理器的最终状态为准进行展示，避免显示与实际不一致
        status = self.processor.get_multithreading_status()
        print(f"🚀 多线程下载: {'启用' if status['enabled'] else '禁用'}")
        if status['enabled']:
            print(f"🔧 线程数: {status['max_threads']}")

        # 显示输出位置（绝对路径）
        from pathlib import Path
        output_location = self.settings['output_folder'] if self.settings['output_folder'] else 'output'
        output_abs_path = Path(output_location).resolve()
        print(f"\n📁 输出目录: {output_abs_path}")
        print(f"💾 图片将保存在: {output_abs_path}/company_id/account_id/user_id/")
        print(f"🚀 开始下载图片...\n")

        # 根据筛选方式选择处理方法
        if filtered_data:
            # 使用智能筛选的数据
            success = self.process_filtered_data(
                filtered_data['dataframe'],
                file_path,
                self.settings['output_folder']
            )
        else:
            # 使用传统的账户筛选
            success = self.processor.process_single_file(
                file_path,
                self.settings['output_folder'],
                account_filter=account_filter
            )

        if success:
            print("\n" + "=" * 60)
            print("✅ 文件处理完成！")
            print("=" * 60)
            print(f"📁 文件保存位置: {output_abs_path}")

            # 显示输出文件路径
            input_path = Path(file_path)
            if filtered_data:
                output_file = output_abs_path / f"{input_path.stem}_filtered.xlsx"
            else:
                output_file = output_abs_path / f"{input_path.stem}_updated.xlsx"
            print(f"📄 数据文件: {output_file}")
            print(f"🖼️  图片目录: {output_abs_path}/company_id/account_id/user_id/")
            print("=" * 60)
        else:
            print("❌ 文件处理失败，请查看日志文件")

    def handle_batch_files(self):
        """批量处理文件夹"""
        print("\n📁 批量文件处理")
        print("-" * 30)

        # 获取文件夹路径
        folder_path = input("请输入文件夹路径: ").strip()

        if not folder_path:
            print("❌ 文件夹路径不能为空")
            return

        # 处理路径中的引号
        folder_path = folder_path.strip("'\"")

        # 展开用户目录路径
        folder_path = os.path.expanduser(folder_path)

        if not os.path.exists(folder_path):
            print(f"❌ 文件夹不存在: {folder_path}")
            print(f"🔍 检查路径: {os.path.abspath(folder_path)}")
            return

        # 检查账户筛选
        account_filter = self.settings['account_filter']
        if account_filter is None:
            # 交互式设置账户筛选
            account_filter = self.interactive_account_filter_setup()
            if account_filter is False:  # 用户选择取消
                return
            # 如果用户选择了筛选条件，account_filter 现在包含筛选列表或 None（全量处理）

        print(f"\n🔄 开始批量处理文件夹: {folder_path}")

        # 显示输出位置（绝对路径）
        from pathlib import Path
        output_location = self.settings['output_folder'] if self.settings['output_folder'] else 'output'
        output_abs_path = Path(output_location).resolve()

        print(f"🔍 递归搜索: {'启用' if self.settings['recursive'] else '禁用'}")
        if account_filter:
            print(f"🔍 账户筛选: {', '.join(account_filter)}")
        else:
            print("🔍 处理模式: 全量处理（所有账户）")
        # 应用多线程设置（使用配置或用户设置）
        self.processor.set_multithreading_enabled(self.settings['multithreading_enabled'])
        self.processor.set_max_threads(self.settings['max_threads'])
        self.processor.set_download_timeout(self.settings['download_timeout'])

        # 以处理器的最终状态为准进行展示，避免显示与实际不一致
        status = self.processor.get_multithreading_status()
        print(f"🚀 多线程下载: {'启用' if status['enabled'] else '禁用'}")
        if status['enabled']:
            print(f"🔧 线程数: {status['max_threads']}")

        print(f"\n📁 输出目录: {output_abs_path}")
        print(f"💾 所有文件将保存在: {output_abs_path}")
        print(f"🚀 开始批量下载图片...\n")

        results = self.processor.process_batch_files(
            folder_path,
            self.settings['output_folder'],
            self.settings['recursive'],
            account_filter=account_filter
        )

        print("\n" + "=" * 60)
        print("✅ 批量处理完成！")
        print("=" * 60)
        print(f"📊 处理统计:")
        print(f"  总文件数: {results['total']}")
        print(f"  成功处理: {results['success']}")
        print(f"  处理失败: {results['failed']}")
        print(f"\n📁 文件保存位置: {output_abs_path}")
        print(f"🖼️  图片目录结构: {output_abs_path}/company_id/account_id/user_id/")
        print("=" * 60)

    def handle_view_folder(self):
        """查看文件夹内容"""
        print("\n👀 查看文件夹内容")
        print("-" * 30)

        folder_path = input("请输入文件夹路径: ").strip()

        if not folder_path:
            print("❌ 文件夹路径不能为空")
            return

        # 处理路径中的引号
        folder_path = folder_path.strip("'\"")

        # 展开用户目录路径
        folder_path = os.path.expanduser(folder_path)

        if not os.path.exists(folder_path):
            print(f"❌ 文件夹不存在: {folder_path}")
            print(f"🔍 检查路径: {os.path.abspath(folder_path)}")
            return

        files = self.processor.find_data_files(folder_path, recursive=False)

        print(f"\n📁 文件夹 {folder_path} 中的数据文件:")
        if files:
            for i, file_path in enumerate(files, 1):
                file_format = self.processor.detect_file_format(file_path)
                print(f"  {i}. {file_path} ({file_format})")
        else:
            print("  (没有找到支持的数据文件)")

    def handle_detect_format(self):
        """检测文件格式"""
        print("\n🔍 检测文件格式")
        print("-" * 30)

        file_path = input("请输入文件路径: ").strip()

        if not file_path:
            print("❌ 文件路径不能为空")
            return

        # 处理路径中的引号
        file_path = file_path.strip("'\"")

        # 展开用户目录路径
        file_path = os.path.expanduser(file_path)

        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            print(f"🔍 检查路径: {os.path.abspath(file_path)}")
            return

        file_format = self.processor.detect_file_format(file_path)
        print(f"📄 文件 {file_path} 的格式: {file_format}")

    def handle_settings(self):
        """设置配置"""
        while True:
            print("\n⚙️ 设置配置")
            print("-" * 30)
            print("  1. 设置输出文件夹")
            print("  2. 设置递归搜索")
            print("  3. 设置账户筛选")
            print("  4. 清除账户筛选")
            print("  5. 多线程下载设置")
            print("  6. 重置为默认配置")
            print("  7. 清理日志文件")
            print("  8. 返回主菜单")

            choice = self.get_user_choice(8)
            if choice == -1:
                return

            if choice == 1:
                self.set_output_folder()
            elif choice == 2:
                self.set_recursive()
            elif choice == 3:
                self.set_account_filter()
            elif choice == 4:
                self.clear_account_filter()
            elif choice == 5:
                self.handle_multithreading_settings()
            elif choice == 6:
                self.reset_user_settings()
            elif choice == 7:
                self.clean_logs_ui()
            elif choice == 8:
                break

    def clean_logs_ui(self):
        """
        简单的日志清理入口
        """
        try:
            days_str = input("请输入要保留的天数（默认7天，小于等于0表示全部清理）: ").strip()
            days = int(days_str) if days_str else 7
        except Exception:
            days = 7
        try:
            removed = self.processor.clean_logs(retention_days=days)
            print(f"🧹 日志清理完成，删除 {removed} 个历史日志文件（保留{days}天内文件）")
        except Exception as e:
            print(f"❌ 日志清理失败: {e}")

    def set_output_folder(self):
        """设置输出文件夹"""
        current = self.settings['output_folder']
        print(f"\n当前输出文件夹: {current}")
        new_folder = input("请输入新的输出文件夹路径: ").strip()

        if new_folder:
            self.settings['output_folder'] = new_folder
            self.save_user_settings()
            print(f"✅ 输出文件夹已设置为: {new_folder}")
        else:
            print("❌ 路径不能为空")

    def set_recursive(self):
        """设置递归搜索"""
        current = "启用" if self.settings['recursive'] else "禁用"
        print(f"\n当前递归搜索: {current}")
        print("1. 启用递归搜索")
        print("2. 禁用递归搜索")

        choice = self.get_user_choice(2)
        if choice == 1:
            self.settings['recursive'] = True
            self.save_user_settings()
            print("✅ 递归搜索已启用")
        elif choice == 2:
            self.settings['recursive'] = False
            self.save_user_settings()
            print("✅ 递归搜索已禁用")

    def set_account_filter(self):
        """设置账户筛选"""
        print("\n设置账户筛选")
        print("请输入要筛选的账户ID")
        print("💡 支持格式:")
        print("   - 基本格式: 1001,1002,1003")
        print("   - 带引号: '27498125528840,'1002,'1003")
        print("   - 空格分隔: '27498125528840 1002 1003")
        print("   - 中文逗号: '27498125528840，1002，1003")

        ids_input = input("账户ID: ").strip()

        if not ids_input:
            print("❌ 输入不能为空")
            return

        # 解析账户ID，支持多种格式
        ids = self.parse_account_ids(ids_input)

        if ids:
            self.settings['account_filter'] = ids
            self.save_user_settings()
            print(f"✅ 已设置账户筛选: {', '.join(ids)}")
        else:
            print("❌ 未找到有效的账户ID")

    def clear_account_filter(self):
        """清除账户筛选"""
        self.settings['account_filter'] = None
        self.save_user_settings()
        print("✅ 已清除账户筛选")

    def handle_multithreading_settings(self):
        """处理多线程设置"""
        while True:
            print("\n🚀 多线程下载设置")
            print("-" * 30)
            current_status = "启用" if self.settings['multithreading_enabled'] else "禁用"
            print(f"当前状态: {current_status}")
            print(f"最大线程数: {self.settings['max_threads']}")
            print(f"下载超时: {self.settings['download_timeout']} 秒")
            print()
            print("  1. 启用/禁用多线程下载")
            print("  2. 设置最大线程数")
            print("  3. 设置下载超时时间")
            print("  4. 返回上级菜单")

            choice = self.get_user_choice(4)
            if choice == -1:
                return

            if choice == 1:
                self.toggle_multithreading()
            elif choice == 2:
                self.set_max_threads()
            elif choice == 3:
                self.set_download_timeout()
            elif choice == 4:
                break

    def toggle_multithreading(self):
        """切换多线程启用状态"""
        current = self.settings['multithreading_enabled']
        print(f"\n当前多线程下载: {'启用' if current else '禁用'}")
        print("1. 启用多线程下载")
        print("2. 禁用多线程下载")

        choice = self.get_user_choice(2)
        if choice == 1:
            self.settings['multithreading_enabled'] = True
            self.processor.set_multithreading_enabled(True)
            self.save_user_settings()
            print("✅ 多线程下载已启用")
        elif choice == 2:
            self.settings['multithreading_enabled'] = False
            self.processor.set_multithreading_enabled(False)
            self.save_user_settings()
            print("✅ 多线程下载已禁用")

    def set_max_threads(self):
        """设置最大线程数"""
        print(f"\n当前最大线程数: {self.settings['max_threads']}")
        print("建议范围: 2-12 个线程")

        try:
            new_threads = int(input("请输入新的最大线程数: ").strip())
            if new_threads < 1:
                print("❌ 线程数不能小于 1")
                return
            elif new_threads > 20:
                print("❌ 线程数不能大于 20")
                return

            self.settings['max_threads'] = new_threads
            self.processor.set_max_threads(new_threads)
            self.save_user_settings()
            print(f"✅ 最大线程数已设置为: {new_threads}")

        except ValueError:
            print("❌ 请输入有效的数字")

    def set_download_timeout(self):
        """设置下载超时时间"""
        print(f"\n当前下载超时时间: {self.settings['download_timeout']} 秒")
        print("建议范围: 30-300 秒")

        try:
            new_timeout = int(input("请输入新的超时时间（秒）: ").strip())
            if new_timeout < 10:
                print("❌ 超时时间不能小于 10 秒")
                return
            elif new_timeout > 600:
                print("❌ 超时时间不能大于 600 秒")
                return

            self.settings['download_timeout'] = new_timeout
            self.processor.set_download_timeout(new_timeout)
            self.save_user_settings()
            print(f"✅ 下载超时时间已设置为: {new_timeout} 秒")

        except ValueError:
            print("❌ 请输入有效的数字")

    def show_settings(self):
        """显示当前设置"""
        print("\n📊 当前设置:")
        print("-" * 30)
        print(f"  输出文件夹: {self.settings['output_folder']}")
        print(f"  递归搜索: {'启用' if self.settings['recursive'] else '禁用'}")
        account_filter = self.settings['account_filter']
        if account_filter:
            print(f"  账户筛选: {', '.join(account_filter)}")
        else:
            print("  账户筛选: 未设置（处理时可选择筛选或全量）")
        print(f"  多线程下载: {'启用' if self.settings['multithreading_enabled'] else '禁用'}")
        print(f"  最大线程数: {self.settings['max_threads']}")
        print(f"  下载超时: {self.settings['download_timeout']} 秒")

    def run(self):
        """运行简单模式"""
        self.print_welcome()

        while True:
            try:
                self.print_main_menu()
                choice = self.get_user_choice(7)

                if choice == -1:  # Ctrl+C
                    break
                elif choice == 1:
                    self.handle_single_file()
                elif choice == 2:
                    self.handle_batch_files()
                elif choice == 3:
                    self.handle_view_folder()
                elif choice == 4:
                    self.handle_detect_format()
                elif choice == 5:
                    self.handle_settings()
                elif choice == 6:
                    self.show_settings()
                elif choice == 7:
                    print("👋 返回主程序")
                    break

                # 询问是否继续
                print("\n" + "-" * 40)
                continue_choice = input("按回车键继续，或输入 'q' 退出: ").strip().lower()
                if continue_choice == 'q':
                    break

            except KeyboardInterrupt:
                print("\n\n👋 程序已退出")
                break
            except Exception as e:
                print(f"\n❌ 处理过程中出现错误: {e}")
                print("请重试或返回主程序")


    def interactive_account_filter_setup(self):
        """交互式账户筛选设置"""
        print("\n🔍 账户筛选设置")
        print("-" * 30)
        print("请选择处理方式:")
        print("  1. 设置账户筛选 (只处理指定账户)")
        print("  2. 全量处理 (处理所有账户数据)")
        print("  3. 进入设置菜单进行详细配置")
        print("  4. 取消处理")

        choice = self.get_user_choice(4)
        if choice == -1:
            return None

        if choice == 1:
            # 直接设置账户筛选
            print("\n请输入要筛选的账户ID:")
            print("💡 支持格式:")
            print("   - 基本格式: 1001,1002,1003")
            print("   - 带引号: '27498125528840,'1002,'1003")
            print("   - 空格分隔: '27498125528840 1002 1003")
            print("   - 中文逗号: '27498125528840，1002，1003")
            account_input = input("账户ID列表: ").strip()

            if not account_input:
                print("❌ 账户ID不能为空")
                return self.interactive_account_filter_setup()  # 重新选择

            try:
                # 解析账户ID列表，支持多种格式
                account_list = self.parse_account_ids(account_input)
                if not account_list:
                    print("❌ 请输入有效的账户ID")
                    return self.interactive_account_filter_setup()  # 重新选择

                # 临时设置账户筛选（不保存到全局设置）
                print(f"✅ 已设置账户筛选: {', '.join(account_list)}")
                return account_list

            except Exception as e:
                print(f"❌ 账户ID格式错误: {e}")
                return self.interactive_account_filter_setup()  # 重新选择

        elif choice == 2:
            # 全量处理
            print("✅ 将处理所有账户数据")
            return None  # None 表示不筛选

        elif choice == 3:
            # 进入设置菜单
            print("\n🔄 进入账户筛选设置...")
            self.set_account_filter()
            return self.settings['account_filter']

        elif choice == 4:
            # 取消处理
            print("❌ 已取消处理")
            return False  # False 表示取消

        return None


def main():
    """主函数"""
    processor = SimpleProcessor()
    processor.run()


if __name__ == "__main__":
    main()
