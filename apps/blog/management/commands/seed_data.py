from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User, UserRole, UserStatus, Profile
from blog.models import Category, Tag, Blog, BlogStatus, Comment, Like
from content.models import SiteSetting

class Command(BaseCommand):
    help = 'Seeds database with initial categories, tags, site settings, users, and sample blog posts.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding database..."))

        # 1. Site Settings
        settings = SiteSetting.get_settings()
        settings.site_name = "Blogs Monkey"
        settings.site_description = "The next-generation editorial platform for developers, designers, and SaaS founders."
        settings.hero_headline = "Publishing engineered for modern creators."
        settings.hero_subheadline = "Write, curate, and scale your publication with linear-style cleanliness and lightning-fast reader UX."
        settings.contact_email = "sanskarkumar871@gamil.com"
        settings.save()
        self.stdout.write(self.style.SUCCESS("[OK] Site settings initialized."))

        # 2. Users
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@blogsmonkey.com',
                'first_name': 'Alexander',
                'last_name': 'Vance',
                'role': UserRole.ADMIN,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123456')
            admin_user.save()
            admin_user.profile.bio = "Founder & Chief Editor at Blogs Monkey. Engineering scaled web architectures and modern SaaS products."
            admin_user.profile.save()
            self.stdout.write(self.style.SUCCESS("[OK] Admin user created (admin / admin123456)."))

        author1, created = User.objects.get_or_create(
            username='dev_marcus',
            defaults={
                'email': 'marcus@blogsmonkey.com',
                'first_name': 'Marcus',
                'last_name': 'Chen',
                'role': UserRole.AUTHOR,
            }
        )
        if created:
            author1.set_password('author123456')
            author1.save()
            author1.profile.bio = "Senior Backend Architect specializing in Python, Django, and distributed MySQL databases."
            author1.profile.save()
            self.stdout.write(self.style.SUCCESS("[OK] Author 'dev_marcus' created (dev_marcus / author123456)."))

        author2, created = User.objects.get_or_create(
            username='sarah_ux',
            defaults={
                'email': 'sarah@blogsmonkey.com',
                'first_name': 'Sarah',
                'last_name': 'Jenkins',
                'role': UserRole.AUTHOR,
            }
        )
        if created:
            author2.set_password('author123456')
            author2.save()
            author2.profile.bio = "Design Director & Front-end Specialist focused on micro-animations and editorial typography."
            author2.profile.save()
            self.stdout.write(self.style.SUCCESS("[OK] Author 'sarah_ux' created (sarah_ux / author123456)."))

        # 3. Categories (12 Default Categories)
        categories_def = [
            ('Engineering', 'Deep dives into system design, backend architectures, and database scalability.', 'code'),
            ('Design & UX', 'Crafting visual interfaces, typographic harmony, and modern micro-animations.', 'layout'),
            ('Artificial Intelligence', 'Exploring practical LLM integrations, AI tools, and machine learning infrastructure.', 'cpu'),
            ('SaaS & Business', 'Actionable frameworks for building, bootstrapping, and scaling SaaS apps.', 'trending-up'),
            ('Web Development', 'Frontend engineering, modern CSS, JavaScript frameworks, and web standards.', 'globe'),
            ('Data Science', 'Data analytics, SQL optimizations, machine learning pipelines, and big data.', 'database'),
            ('DevOps & Cloud', 'CI/CD pipelines, Docker containers, Kubernetes, and cloud infrastructure.', 'server'),
            ('Mobile Development', 'iOS, Android, React Native, and Flutter app development.', 'smartphone'),
            ('Cybersecurity', 'Application security, OAuth2, data privacy, and encryption best practices.', 'shield'),
            ('Career & Productivity', 'Developer workflows, team culture, career growth, and remote work strategies.', 'zap'),
            ('Marketing & Growth', 'SEO optimization, content strategy, developer marketing, and user acquisition.', 'bar-chart-2'),
            ('General & Personal', 'Miscellaneous thoughts, personal experiences, and un-categorized topics.', 'feather'),
        ]
        created_cats = {}
        for name, desc, icon in categories_def:
            cat_obj, _ = Category.objects.get_or_create(
                name=name,
                defaults={'description': desc, 'icon_name': icon}
            )
            created_cats[name] = cat_obj
        
        cat_eng = created_cats['Engineering']
        cat_design = created_cats['Design & UX']
        cat_ai = created_cats['Artificial Intelligence']
        cat_saas = created_cats['SaaS & Business']
        self.stdout.write(self.style.SUCCESS("[OK] 12 Default Categories initialized."))

        # 4. Tags
        tag_django = Tag.objects.get_or_create(name='Django')[0]
        tag_python = Tag.objects.get_or_create(name='Python')[0]
        tag_mysql = Tag.objects.get_or_create(name='MySQL')[0]
        tag_tailwind = Tag.objects.get_or_create(name='TailwindCSS')[0]
        tag_architecture = Tag.objects.get_or_create(name='Architecture')[0]
        tag_ux = Tag.objects.get_or_create(name='UI/UX')[0]
        tag_saas = Tag.objects.get_or_create(name='SaaS')[0]
        self.stdout.write(self.style.SUCCESS("[OK] Tags created."))

        # 5. Blog Posts
        posts_data = [
            {
                'title': 'Building Scalable Django Architectures in 2026',
                'excerpt': 'Discover key architectural patterns for structuring high-concurrency Django SaaS applications with clean application boundaries.',
                'content': '''<p class="lead">Building production-grade web applications in Django requires careful consideration of model boundary isolation, query optimization, and frontend integration.</p>
<h2>1. Keep Django Apps Focused and Lean</h2>
<p>One of the most common pitfalls in Django project layout is creating dozens of granular apps for minor utilities. Instead, group domain boundaries into 4-6 primary apps such as <code>accounts</code>, <code>blog</code>, <code>content</code>, and <code>dashboard</code>.</p>
<h2>2. Database Query Optimization with Django ORM</h2>
<p>Always leverage <code>select_related</code> for ForeignKey relations and <code>prefetch_related</code> for ManyToMany fields to prevent N+1 query bottlenecks.</p>
<pre><code># Optimized queryset
blogs = Blog.published.select_related('author', 'category').prefetch_related('tags')
</code></pre>
<h2>3. Hybrid Server-Driven Interactive UI</h2>
<p>By pairing Django templates with <strong>Tailwind CSS</strong>, <strong>HTMX</strong>, and <strong>Alpine.js</strong>, you can achieve single-page app responsiveness without JavaScript framework overhead.</p>''',
                'author': admin_user,
                'category': cat_eng,
                'tags': [tag_django, tag_python, tag_architecture],
                'status': BlogStatus.PUBLISHED,
                'is_featured': True,
                'is_trending': True,
                'view_count': 1420,
            },
            {
                'title': 'Mastering MySQL 8 Indexing & Query Tuning for Web Platforms',
                'excerpt': 'A comprehensive guide to composite indexes, JSON column efficiency, and query execution plans in MySQL for SaaS backends.',
                'content': '''<p class="lead">Database performance dictates your user experience. In high-traffic SaaS applications, unindexed columns can turn a 2ms query into a 3-second database lock.</p>
<h2>Composite Indexing Strategy</h2>
<p>When filtering by status and ordering by published date, create a compound index across both columns:</p>
<pre><code>CREATE INDEX blog_status_pubdate_idx ON blog_blog (status, published_at DESC);</code></pre>
<p>This allows MySQL to perform range scans without temporary filesort operations.</p>''',
                'author': author1,
                'category': cat_eng,
                'tags': [tag_mysql, tag_architecture, tag_python],
                'status': BlogStatus.PUBLISHED,
                'is_featured': True,
                'is_trending': False,
                'view_count': 890,
            },
            {
                'title': 'Designing Linear-Style Glassmorphism & Micro-Animations',
                'excerpt': 'How to craft subtle borders, soft ambient lighting, and fluid hover states that elevate editorial reading experiences.',
                'content': '''<p class="lead">Modern web aesthetics in 2026 prioritize generous whitespace, sleek dark-mode contrast, and tactile feedback.</p>
<h2>Clean Typography and Line Height</h2>
<p>Editorial content should feel effortless to read. Maintain a line-height ratio of 1.75 for body text and contrast headings with bold weights.</p>
<h2>Soft ambient borders</h2>
<p>Use semi-transparent borders such as <code>border-slate-200/80 dark:border-slate-800/80</code> to create depth without clutter.</p>''',
                'author': author2,
                'category': cat_design,
                'tags': [tag_tailwind, tag_ux],
                'status': BlogStatus.PUBLISHED,
                'is_featured': False,
                'is_trending': True,
                'view_count': 2150,
            },
            {
                'title': 'The Modern SaaS Tech Stack: Django, HTMX & Alpine.js',
                'excerpt': 'Why modern development teams are shifting back to server-rendered Django apps powered by HTMX for hyper-fast iteration.',
                'content': '''<p class="lead">Heavy client-side bundles are often unnecessary for content-focused SaaS applications. HTMX allows you to swap DOM fragments straight from Django views with minimal code.</p>''',
                'author': author1,
                'category': cat_saas,
                'tags': [tag_django, tag_saas, tag_tailwind],
                'status': BlogStatus.PUBLISHED,
                'is_featured': False,
                'is_trending': False,
                'view_count': 630,
            },
            {
                'title': 'Integrating AI-Powered Content Summarization in SaaS Apps',
                'excerpt': 'A step-by-step walkthrough of incorporating background LLM processing for automatic article summary generation.',
                'content': '''<p class="lead">Drafting compelling summaries can be automated using LLM completion APIs. Here is how we design asynchronous job pipelines in Python.</p>''',
                'author': author1,
                'category': cat_ai,
                'tags': [tag_python, tag_saas],
                'status': BlogStatus.PENDING_REVIEW,
                'is_featured': False,
                'is_trending': False,
                'view_count': 0,
            },
            {
                'title': 'Drafting the Next Era of Technical Writing',
                'excerpt': 'Early draft on the future of technical documentation and developer blogs.',
                'content': '''<p>This is a work in progress draft exploring how AI tools assist technical writers in structuring documentation.</p>''',
                'author': author2,
                'category': cat_design,
                'tags': [tag_ux],
                'status': BlogStatus.DRAFT,
                'is_featured': False,
                'is_trending': False,
                'view_count': 0,
            }
        ]

        for p_data in posts_data:
            tags_list = p_data.pop('tags')
            blog, created = Blog.objects.get_or_create(
                title=p_data['title'],
                defaults=p_data
            )
            if created:
                blog.tags.set(tags_list)
                if blog.status == BlogStatus.PUBLISHED:
                    blog.published_at = timezone.now()
                    blog.save()
                    # Add sample comments & likes
                    Comment.objects.create(
                        blog=blog,
                        author=admin_user,
                        content="Fantastic article! The insights on query optimization are spot on."
                    )
                    Like.objects.create(blog=blog, user=admin_user)

        self.stdout.write(self.style.SUCCESS("[OK] Seeded sample blog posts, comments, and likes successfully."))
        self.stdout.write(self.style.SUCCESS("\n== SEED COMPLETE =="))
        self.stdout.write(self.style.SUCCESS("Admin Credentials: Username: 'admin' | Password: 'admin123456'"))
        self.stdout.write(self.style.SUCCESS("Author Credentials: Username: 'dev_marcus' | Password: 'author123456'"))
