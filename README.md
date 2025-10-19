Django app that helps you charm your app



tested: flask with .tar file

need to test:
- other frameworks
- github

Need to update integration selection
Need to wire selected integrations to the charmcraft.yaml file
Need to wire added config options to the charmcraft.yaml file
Need to clean the repo and set it up for Django app only.



launch.json:

{
  // Use IntelliSense to learn about possible attributes.
  // Hover to view descriptions of existing attributes.
  // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python Debugger: Django",
      "type": "debugpy",
      "request": "launch",
      "program": "${workspaceFolder}/django_app/manage.py",
      "args": ["runserver", "8001"],
      "django": true,
      "justMyCode": true
    }
  ]
}
