from invoke import task
import boto3
import fileinput

@task
def start(c):
    """
    Starts the development containers
    """
    c.run('lando start')

@task
def update(c, site='demoplus'):
    """
    Pull down and update all content, including database and files.
    """
    c.run('lando db-import dumps/{}.database.sql'.format(site))
    drush(c, 'updb -y')
    drush(c, 'cr')

@task
def savedb(c, site='demoplus', sanitize=True):
    if sanitize:
        sanitize_config(c)
    c.run('lando db-export dumps/{}.database.sql'.format(site))
    c.run('gunzip -f dumps/{}.database.sql.gz'.format(site))
    if sanitize:
        c.run('sed -i "s/@acromedia\\(inc\\)\\?/@example/g"\
           ./dumps/{}.database.sql'.format(site))

@task
def sanitize_config(c):
    drush(c, 'cex --destination=/tmp/config-export -y')
    c.run('lando ssh -c "find /tmp/config-export -type f -name \'*.yml\' -exec\
           sed -i \'s/@acromedia\\(inc\\)\\?/@example/g\' {} ;"')
    drush(c, 'cim --source=/tmp/config-export --partial -y')
    c.run('lando ssh -c "rm -rf /tmp/config-export"')
    drush(c, 'cr')

@task(post=[start, update])
def setup(c):
    c.run('lando composer install')
    c.run('cp web/sites/default/example.settings.local.php web/sites/default/settings.local.php')
    c.run('tar -xzf dumps/files.tar.gz -C web/sites/default')

@task(help={
    'command':'The command to run through drush. Multiple parameters can be passed in quotes. Example : `inv drush "updb -y"`'
})
def drush(c, command):
    """
    Pipes drush commands into the container
    """
    c.run("lando drush {}".format(command), pty=True)

@task
def solrconfig(c):
    c.run("lando drush solr-gsc solr ../solr-config.zip")
    c.run("lando ssh -c 'unzip solr-config.zip -d solr-config'")
    c.run("touch solr-config/mapping-ISOLatin1Accent.txt")
    c.run("touch solr-config/synonyms.txt")
    c.run("touch solr-config/stopwords.txt")
    c.run("touch solr-config/protwords.txt")
    c.run("lando ssh -s search -c 'solr create_core -c orange -d solr-config'")
    c.run("rm solr-config -rf")