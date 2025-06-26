# Generated manually for vector database integration

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('app_doc', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentVector',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vector_id', models.CharField(max_length=100, verbose_name='向量ID')),
                ('content_hash', models.CharField(max_length=64, verbose_name='内容哈希')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('doc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app_doc.doc', verbose_name='文档')),
            ],
            options={
                'verbose_name': '文档向量',
                'verbose_name_plural': '文档向量',
            },
        ),
        migrations.CreateModel(
            name='VectorCollection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='集合名称')),
                ('dimension', models.IntegerField(default=1536, verbose_name='向量维度')),
                ('description', models.TextField(blank=True, null=True, verbose_name='描述')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否激活')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
            ],
            options={
                'verbose_name': '向量集合',
                'verbose_name_plural': '向量集合',
            },
        ),
        migrations.AlterUniqueTogether(
            name='documentvector',
            unique_together={('doc', 'vector_id')},
        ),
        migrations.AddIndex(
            model_name='documentvector',
            index=models.Index(fields=['doc'], name='app_vector_d_doc_id_12345678_idx'),
        ),
        migrations.AddIndex(
            model_name='documentvector',
            index=models.Index(fields=['content_hash'], name='app_vector_d_content_12345678_idx'),
        ),
    ] 