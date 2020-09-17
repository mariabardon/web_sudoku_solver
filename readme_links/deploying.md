These are only the step I followed to deploy in heroku, once my Django app was ready and had all the necessary changes to be deployed. A good guide that can help you with getting your Django app ready for heroku can be found in [medium](https://medium.com/@selfengineeredd/step-by-step-guide-on-how-to-deploy-a-django-app-to-heroku-c28d746043ee).

Just remember not to include a pytorch for cuda version in the requirements as it is not necessary any more at this stage, and it will take too much space.

The steps that I followed to deploy  my app are these:
1. Create heroku app following steps above
2. Set aws credentials as enviromental variables [here](https://devcenter.heroku.com/articles/config-vars)
3. Commit and push my app to heroku master.
$git add .
$git push heroku master
4. Create a jvm buildpack in heroku [here](https://elements.heroku.com/buildpacks/heroku/heroku-buildpack-jvm-common)
$ heroku buildpacks:add --index 2 heroku/jvm
5. Commit and push without changes to heroku:
$git commit --allow-empty -m "Deploy again"
$git push heroku master

or simply

$heroku restart --app app_name

6. Change my dyno to hobby on the web console
7. Set the WEB_CONCURRENCY variable to 3 in heroku [here](https://devcenter.heroku.com/articles/python-gunicorn)
$heroku config:set WEB_CONCURRENCY=3
