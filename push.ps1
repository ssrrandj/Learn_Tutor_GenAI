param(
    [string]$msg = "Auto Commit"
)

git add .
git commit -m "Auto Commit"
git push origin main